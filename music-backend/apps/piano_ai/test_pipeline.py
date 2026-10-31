import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
import xml.etree.ElementTree as ET

import pretty_midi
from fastapi.testclient import TestClient

# Isolate uploaded files and status records from real songs.
TEMP = tempfile.TemporaryDirectory(prefix='piano-api-tests-')
os.environ['PIANO_JOBS_DIR'] = TEMP.name
from .api import app  # noqa: E402
from .pipeline import PipelineError, youtube_url  # noqa: E402


def fixture_midi():
    midi = pretty_midi.PrettyMIDI(initial_tempo=100)
    instrument = pretty_midi.Instrument(0)
    # Includes both range extremes, a sharp, and the C4 staff boundary.
    for index, pitch in enumerate((21, 48, 60, 61, 64, 67, 84, 108)):
        instrument.notes.append(pretty_midi.Note(90, pitch, index * 0.6, index * 0.6 + 0.5))
    midi.instruments.append(instrument)
    data = io.BytesIO()
    midi.write(data)
    return data.getvalue()


class PianoApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_youtube_canonicalization(self):
        self.assertEqual(youtube_url('https://youtu.be/abcdefghijk?t=10'), 'https://www.youtube.com/watch?v=abcdefghijk')
        for invalid in ('file:///etc/passwd', 'http://127.0.0.1/watch?v=abcdefghijk',
                        'https://youtube.com.evil.test/watch?v=abcdefghijk',
                        'https://www.youtube.com/playlist?list=abc', 'https://youtube.com:444/watch?v=abcdefghijk'):
            with self.subTest(invalid=invalid), self.assertRaises(PipelineError):
                youtube_url(invalid)

    def test_invalid_submissions(self):
        self.assertEqual(self.client.post('/jobs').status_code, 400)
        self.assertEqual(self.client.post('/jobs', files={'file': ('bad.exe', b'hello')}).status_code, 400)
        self.assertEqual(self.client.post('/jobs', files={'file': ('empty.wav', b'')}).status_code, 400)
        self.assertEqual(self.client.post('/jobs', data={'youtube': 'https://example.com/test'}).status_code, 400)
        self.assertEqual(self.client.get('/jobs/not-a-uuid').status_code, 404)

    def test_mobile_cors(self):
        for origin in ('http://192.168.1.20:8081', 'http://10.0.0.20:8082', 'null'):
            response = self.client.get('/health', headers={'Origin': origin})
            self.assertEqual(response.headers.get('access-control-allow-origin'), origin)
        response = self.client.get('/health', headers={'Origin': 'https://unrelated.example.com'})
        self.assertNotIn('access-control-allow-origin', response.headers)

    def test_midi_to_score_and_playback(self):
        response = self.client.post('/jobs', files={'file': ('Piano <test>.mid', fixture_midi(), 'audio/midi')})
        self.assertEqual(response.status_code, 202, response.text)
        job_id = response.json()['id']
        for _ in range(200):
            state = self.client.get(f'/jobs/{job_id}').json()
            if state['status'] in {'completed', 'failed'}:
                break
            time.sleep(0.05)
        if state['status'] == 'failed':
            self.fail((Path(TEMP.name) / job_id / 'error.log').read_text(encoding='utf-8'))
        self.assertEqual(state['status'], 'completed', state)
        self.assertIn('timings', state)
        self.assertIn('analyzing', state['timings']['stagesSeconds'])
        self.assertIn('engraving', state['timings']['stagesSeconds'])
        timing_file = Path(TEMP.name) / job_id / 'timings.json'
        for _ in range(20):
            if timing_file.is_file():
                break
            time.sleep(0.01)
        self.assertTrue(timing_file.is_file())
        self.assertGreater(json.loads(timing_file.read_text(encoding='utf-8'))['elapsedSeconds'], 0)
        result = self.client.get(f'/jobs/{job_id}/result').json()
        self.assertEqual(len(result['notes']), 8)
        self.assertTrue(result['pages'])
        self.assertTrue(result['timeline'])
        self.assertAlmostEqual(result['notes'][1]['start'], 0.6, places=3)
        self.assertTrue(all(0 <= note['start'] < note['end'] <= result['duration'] for note in result['notes']))
        self.assertEqual(len([note for note in result['notes'] if note['pitch'] == 60]), 1)
        svg = self.client.get(f'/jobs/{job_id}/assets/{result["pages"][0]}')
        self.assertEqual(svg.status_code, 200)
        root = ET.fromstring(svg.text)
        ids = {element.attrib['id'] for element in root.iter() if 'id' in element.attrib}
        self.assertTrue(set(result['timeline'][0]['on']) <= ids, 'Playback IDs must match rendered score notes')
        midi = self.client.get(f'/jobs/{job_id}/assets/piano.mid')
        self.assertEqual(midi.content[:4], b'MThd')
        self.assertEqual(self.client.get(f'/jobs/{job_id}/assets/worker.log').status_code, 404)
        self.assertEqual(self.client.get(f'/jobs/{job_id}/assets/status.json').status_code, 404)
        self.assertNotIn('HF_TOKEN', json.dumps(result))

    def test_multiple_score_pages_keep_timeline_ids(self):
        midi = pretty_midi.PrettyMIDI(initial_tempo=100)
        instrument = pretty_midi.Instrument(0)
        for index in range(160):
            instrument.notes.append(pretty_midi.Note(90, 48 + index % 24, index * 0.6, index * 0.6 + 0.5))
        midi.instruments.append(instrument)
        data = io.BytesIO()
        midi.write(data)
        response = self.client.post('/jobs', files={'file': ('long.mid', data.getvalue(), 'audio/midi')})
        self.assertEqual(response.status_code, 202)
        job_id = response.json()['id']
        for _ in range(400):
            state = self.client.get(f'/jobs/{job_id}').json()
            if state['status'] in {'completed', 'failed'}:
                break
            time.sleep(0.05)
        self.assertEqual(state['status'], 'completed', state)
        result = self.client.get(f'/jobs/{job_id}/result').json()
        self.assertGreater(len(result['pages']), 1)
        events = [event for event in result['timeline'] if event['on']]
        self.assertEqual(max(event['page'] for event in events), len(result['pages']))
        self.assertGreater(result['duration'], 95)
        for page in range(1, len(result['pages']) + 1):
            svg = self.client.get(f'/jobs/{job_id}/assets/score-{page}.svg')
            ids = {element.get('id') for element in ET.fromstring(svg.text).iter()}
            for event in events:
                if event['page'] == page:
                    self.assertTrue(set(event['on']) <= ids)

    def test_selection_editor_updates_midi_and_preserves_source(self):
        response = self.client.post('/scores', json={'title': 'Edition test', 'bars': 4, 'bpm': 100})
        self.assertEqual(response.status_code, 201, response.text)
        source = response.json()
        row = self.client.get(f'/jobs/{source["id"]}/assets/editor.json').json()[0]
        def edit(song, action, value=None):
            response = self.client.post(f'/jobs/{song["id"]}/edit', json={'selected': [row['id']], 'action': action, 'value': value})
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()
        inserted = edit(source, 'insert', 60)
        self.assertEqual(inserted['notes'][0]['pitch'], 60)
        self.assertAlmostEqual(inserted['notes'][0]['end'], 0.6, delta=0.03)
        self.assertNotEqual(source['id'], inserted['id'])
        sharp = edit(inserted, 'accidental', 'sharp')
        self.assertEqual(sharp['notes'][0]['pitch'], 61)
        half = edit(sharp, 'duration', '2')
        self.assertAlmostEqual(half['notes'][0]['end'], 1.2, delta=0.03)
        dotted = edit(half, 'dot')
        self.assertAlmostEqual(dotted['notes'][0]['end'], 1.8, delta=0.03)
        octave = edit(dotted, 'transpose', 12)
        self.assertEqual(octave['notes'][0]['pitch'], 73)
        accented = edit(octave, 'articulation', 'accent')
        xml = ET.fromstring(self.client.get(f'/jobs/{accented["id"]}/assets/piano.musicxml').content)
        self.assertIsNotNone(xml.find('.//articulations/accent'))
        deleted = edit(accented, 'delete')
        self.assertEqual(deleted['notes'], [])
        self.assertEqual(self.client.get(f'/jobs/{source["id"]}/result').json()['notes'], [])
        self.assertEqual(self.client.get(f'/jobs/{inserted["id"]}/result').json()['notes'][0]['pitch'], 60)
        response = self.client.post(f'/jobs/{inserted["id"]}/edit', json={'selected': ['not-a-note'], 'action': 'delete'})
        self.assertEqual(response.status_code, 400)

    def test_palette_combinations_keep_notation_state(self):
        source = self.client.post('/scores', json={'bars': 2, 'bpm': 100}).json()
        identifier = self.client.get(f'/jobs/{source["id"]}/assets/editor.json').json()[0]['id']

        def edit(song, action, value=None):
            response = self.client.post(f'/jobs/{song["id"]}/edit', json={'selected': [identifier], 'action': action, 'value': value})
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()

        def row(song):
            return next(note for note in self.client.get(f'/jobs/{song["id"]}/assets/editor.json').json() if note['id'] == identifier)

        song = edit(source, 'insert', 60)
        song = edit(song, 'duration', '8')
        song = edit(song, 'dot')
        song = edit(song, 'rest')
        self.assertTrue(row(song)['rest'])
        self.assertEqual((row(song)['duration'], row(song)['dots']), ('eighth', 1))
        song = edit(song, 'rest', 'note')
        self.assertFalse(row(song)['rest'])
        self.assertAlmostEqual(song['notes'][0]['end'], 0.45, delta=0.02)
        song = edit(song, 'voice', 4)
        for articulation in ('accent', 'strong-accent', 'tenuto'):
            song = edit(song, 'articulation', articulation)
        self.assertEqual(row(song)['voice'], '4')
        self.assertEqual(set(row(song)['articulations']), {'accent', 'strong-accent', 'tenuto'})
        song = edit(song, 'articulation', 'accent')
        self.assertEqual(set(row(song)['articulations']), {'strong-accent', 'tenuto'})
        song = edit(song, 'grace', '8:yes')
        grace_rows = self.client.get(f'/jobs/{song["id"]}/assets/editor.json').json()
        self.assertEqual(sum(note['grace'] == '8:yes' for note in grace_rows), 1)
        song = edit(song, 'grace', '8:yes')
        self.assertFalse(any(note['grace'] for note in self.client.get(f'/jobs/{song["id"]}/assets/editor.json').json()))

        from .edition import apply_edit, editor_data
        tree = ET.ElementTree(ET.fromstring('<score-partwise><part><measure number="1"><attributes><divisions>256</divisions></attributes><note id="long-note"><rest/><duration>8192</duration><voice>1</voice><type>long</type></note></measure></part></score-partwise>'))
        for duration, kind in (('0.25', 'long'), ('0.5', 'breve')):
            apply_edit(tree, ['long-note'], 'duration', duration)
            self.assertEqual(editor_data(tree)[0]['duration'], kind)
        apply_edit(tree, ['long-note'], 'dot', None)
        self.assertEqual(editor_data(tree)[0]['dots'], 1)
        self.assertEqual(sum(int(note.findtext('duration')) for note in tree.findall('.//note')), 8192)

    def test_extended_selection_palette(self):
        source = self.client.post('/scores', json={'bars': 2, 'bpm': 100}).json()
        row = self.client.get(f'/jobs/{source["id"]}/assets/editor.json').json()[0]

        def edit(song, action, value=None):
            response = self.client.post(f'/jobs/{song["id"]}/edit', json={'selected': [row['id']], 'action': action, 'value': value})
            self.assertEqual(response.status_code, 200, response.text)
            return response.json()

        inserted = edit(source, 'insert', 60)
        for denominator in ('64', '128', '256', '512'):
            with self.subTest(denominator=denominator):
                short = edit(inserted, 'duration', denominator)
                xml = ET.fromstring(self.client.get(f'/jobs/{short["id"]}/assets/piano.musicxml').content)
                note = next(note for note in xml.findall('.//note') if note.get('id') == row['id'])
                divisions = int(xml.findtext('.//divisions'))
                self.assertEqual(int(note.findtext('duration')) / divisions, 4 / int(denominator))
                self.assertTrue(short['notes'], 'Very short notes must remain playable')
                self.assertAlmostEqual(short['notes'][0]['end'], 0.6 * 4 / int(denominator), delta=0.002)
                dotted = edit(short, 'dot')
                self.assertAlmostEqual(dotted['notes'][0]['end'], 0.9 * 4 / int(denominator), delta=0.002)

        for accidental in ('double-flat', 'double-sharp', 'sharp-sharp'):
            changed = edit(inserted, 'accidental', accidental)
            self.assertEqual(changed['notes'][0]['pitch'], 58 if accidental == 'double-flat' else 62)
        for voice in range(5, 9):
            changed = edit(inserted, 'voice', voice)
            rows = self.client.get(f'/jobs/{changed["id"]}/assets/editor.json').json()
            self.assertEqual(next(note for note in rows if note['id'] == row['id'])['voice'], str(voice))
        for value in ('8:no', '16:yes', '512:no', '512:yes'):
            changed = edit(inserted, 'grace', value)
            xml = ET.fromstring(self.client.get(f'/jobs/{changed["id"]}/assets/piano.musicxml').content)
            grace = xml.find('.//note/grace')
            self.assertIsNotNone(grace)
            self.assertEqual(grace.get('slash'), value.split(':')[1])
            self.assertEqual(xml.find('.//note/grace/..').find('duration'), None)
            self.assertTrue(changed['pages'])

    def test_editor_ties_voices_and_chord_deletion(self):
        source = self.client.post('/scores', json={'bars': 2}).json()
        row = self.client.get(f'/jobs/{source["id"]}/assets/editor.json').json()[0]
        first = self.client.post(f'/jobs/{source["id"]}/edit', json={'selected': [row['id']], 'action': 'insert', 'value': 60}).json()
        rows = self.client.get(f'/jobs/{first["id"]}/assets/editor.json').json()
        rest = next(note for note in rows if note['rest'] and note['measure'] == '1' and note['staff'] == '1')
        second = self.client.post(f'/jobs/{first["id"]}/edit', json={'selected': [rest['id']], 'action': 'insert', 'value': 60}).json()
        tied_response = self.client.post(f'/jobs/{second["id"]}/edit', json={'selected': [row['id'], rest['id']], 'action': 'tie'})
        self.assertEqual(tied_response.status_code, 200, tied_response.text)
        tied = tied_response.json()
        self.assertEqual(len(tied['notes']), 1)
        self.assertAlmostEqual(tied['notes'][0]['end'], 1.2, delta=0.03)
        rows = self.client.get(f'/jobs/{tied["id"]}/assets/editor.json').json()
        remaining = next(note for note in rows if note['rest'] and note['measure'] == '1' and note['staff'] == '1')
        extra = self.client.post(f'/jobs/{tied["id"]}/edit', json={'selected': [remaining['id']], 'action': 'insert', 'value': 64}).json()
        precise = self.client.post(f'/jobs/{extra["id"]}/edit', json={'selected': [remaining['id']], 'action': 'duration', 'value': '512'})
        self.assertEqual(precise.status_code, 200, precise.text)
        self.assertEqual(len(precise.json()['notes']), 2, 'High-resolution playback must preserve tied notes')
        self.assertAlmostEqual(precise.json()['notes'][0]['end'], 1.2, delta=0.002)
        voice = self.client.post(f'/jobs/{first["id"]}/edit', json={'selected': [row['id']], 'action': 'voice', 'value': 4})
        self.assertEqual(voice.status_code, 200, voice.text)
        data = self.client.get(f'/jobs/{voice.json()["id"]}/assets/editor.json').json()
        self.assertEqual(next(note for note in data if note['id'] == row['id'])['voice'], '4')
        midi = pretty_midi.PrettyMIDI(initial_tempo=100)
        inst = pretty_midi.Instrument(0)
        inst.notes = [pretty_midi.Note(90, pitch, 0, 0.6) for pitch in (60, 64, 67)]
        midi.instruments.append(inst)
        stream = io.BytesIO(); midi.write(stream)
        job = self.client.post('/jobs', files={'file': ('chord.mid', stream.getvalue(), 'audio/midi')}).json()
        for _ in range(100):
            state = self.client.get(f'/jobs/{job["id"]}').json()
            if state['status'] in {'completed', 'failed'}:
                break
            time.sleep(0.05)
        self.assertEqual(state['status'], 'completed')
        row = next(note for note in self.client.get(f'/jobs/{job["id"]}/assets/editor.json').json() if note['pitch'] == 60)
        changed = self.client.post(f'/jobs/{job["id"]}/edit', json={'selected': [row['id']], 'action': 'delete'})
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(sorted(note['pitch'] for note in changed.json()['notes']), [64, 67])


if __name__ == '__main__':
    unittest.main()
