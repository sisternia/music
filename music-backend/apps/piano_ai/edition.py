"""MusicXML selection editing. Revisions are immutable and never modify the source job."""
from __future__ import annotations

import base64
import copy
import math
import json
from pathlib import Path
import uuid
import xml.etree.ElementTree as ET

from .pipeline import PipelineError

DURATIONS = {'0.25': 0.25, '0.5': 0.5, **{str(2 ** power): 2 ** power for power in range(10)}}
TYPES = dict(zip(DURATIONS, ('long', 'breve', 'whole', 'half', 'quarter', 'eighth', '16th', '32nd', '64th', '128th', '256th', '512th')))


def normalize_resolution(tree, minimum):
    """Scale all voices and cursor movements equally, preserving exact short-note timing."""
    values = [int(node.text) for node in tree.findall('.//attributes/divisions')]
    target = math.lcm(minimum, *values) if values else math.lcm(minimum, 16)
    for part in tree.findall('.//part'):
        current = 16
        for index, measure in enumerate(part.findall('measure')):
            attributes = measure.find('attributes')
            divisions = attributes.find('divisions') if attributes is not None else None
            if divisions is not None:
                current = int(divisions.text)
                divisions.text = str(target)
            elif index == 0:
                if attributes is None:
                    attributes = ET.Element('attributes')
                    measure.insert(0, attributes)
                ET.SubElement(attributes, 'divisions').text = str(target)
            for node in measure.iter():
                if node.tag in {'duration', 'offset'} and node.text:
                    node.text = str(round(float(node.text) * target / current))
    return target


def identify_score(path: Path):
    tree = ET.parse(path)
    used = set()
    for index, note in enumerate(tree.findall('.//note')):
        identifier = note.get('id') or f'note-{index + 1}'
        if identifier in used:
            identifier = 'note-' + uuid.uuid4().hex[:12]
        note.set('id', identifier)
        used.add(identifier)
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return tree


def pitch_value(note):
    pitch = note.find('pitch')
    if pitch is None:
        return None
    return (int(pitch.findtext('octave', '4')) + 1) * 12 + {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[pitch.findtext('step', 'C')] + int(pitch.findtext('alter', '0'))


def editor_data(tree):
    notes = []
    for measure in tree.findall('.//measure'):
        for note in measure.findall('note'):
            value = pitch_value(note)
            notes.append({'id': note.get('id'), 'pitch': value, 'rest': value is None,
                          'duration': note.findtext('type', 'whole'), 'dots': len(note.findall('dot')),
                          'voice': note.findtext('voice', '1'), 'staff': note.findtext('staff', '1'),
                          'measure': measure.get('number', '1'),
                          'accidental': {'flat-flat': 'double-flat'}.get(note.findtext('accidental'), note.findtext('accidental', '')),
                          'articulations': [child.tag for child in note.findall('notations/articulations/*')],
                          'slur': note.find('notations/slur') is not None,
                          'tie': note.find('tie') is not None,
                          'grace': (next((key for key, kind in TYPES.items() if kind == note.findtext('type')), '8') + ':' + note.find('grace').get('slash', 'no')) if note.find('grace') is not None else ''})
    return notes


def text_child(parent, name, text):
    child = parent.find(name)
    if child is None:
        child = ET.SubElement(parent, name)
    child.text = str(text)
    return child


def set_pitch(note, value):
    if not 21 <= value <= 108:
        raise PipelineError('Cao độ phải nằm trong A0–C8.')
    for rest in note.findall('rest'):
        note.remove(rest)
    pitch = note.find('pitch')
    if pitch is None:
        pitch = ET.Element('pitch')
        note.insert(1 if note.find('chord') is not None else 0, pitch)
    names = [('C', 0), ('C', 1), ('D', 0), ('D', 1), ('E', 0), ('F', 0), ('F', 1), ('G', 0), ('G', 1), ('A', 0), ('A', 1), ('B', 0)]
    step, alter = names[value % 12]
    pitch.clear()
    text_child(pitch, 'step', step)
    if alter:
        text_child(pitch, 'alter', alter)
    text_child(pitch, 'octave', value // 12 - 1)
    for accidental in note.findall('accidental'):
        note.remove(accidental)
    if alter:
        text_child(note, 'accidental', 'sharp')


def set_duration(measure, note, divisions, denominator, dots=0):
    """Keep every voice/bar balanced: borrow adjacent rests or insert a rest when shortening."""
    if note.find('grace') is not None:
        text_child(note, 'type', TYPES[str(denominator)])
        for dot in note.findall('dot'):
            note.remove(dot)
        for _ in range(dots):
            ET.SubElement(note, 'dot')
        return
    old = int(note.findtext('duration', str(divisions * 4)))
    new = round(divisions * 4 / float(denominator) * (2 - 0.5 ** dots))
    if new < 1:
        raise PipelineError('Trường độ nhỏ hơn độ phân giải bản nhạc.')
    voice = note.findtext('voice', '1')
    staff = note.findtext('staff', '1')
    children = list(measure)
    position = children.index(note)
    if note.find('chord') is not None or (position + 1 < len(children) and children[position + 1].find('chord') is not None):
        raise PipelineError('Hãy chọn một nốt đơn để đổi trường độ; hợp âm vẫn có thể đổi cao độ và ký hiệu.')
    if new > old:
        remaining = new - old
        rests = []
        for sibling in children[position + 1:]:
            if sibling.tag != 'note' or sibling.find('rest') is None or sibling.findtext('voice', '1') != voice:
                break
            rests.append(sibling)
        if sum(int(rest.findtext('duration', '0')) for rest in rests) < remaining:
            raise PipelineError('Không đủ dấu lặng kế tiếp trong ô nhịp để tăng trường độ. Chọn trường độ ngắn hơn.')
        for rest in rests:
            duration = int(rest.findtext('duration', '0'))
            if duration <= remaining:
                measure.remove(rest)
                remaining -= duration
            else:
                text_child(rest, 'duration', duration - remaining)
                for kind in rest.findall('type') + rest.findall('dot'):
                    rest.remove(kind)
                remaining = 0
            if not remaining:
                break
    elif new < old:
        rest = ET.Element('note', id='rest-' + uuid.uuid4().hex[:12])
        ET.SubElement(rest, 'rest')
        text_child(rest, 'duration', old - new)
        text_child(rest, 'voice', voice)
        text_child(rest, 'staff', staff)
        measure.insert(position + 1, rest)
    text_child(note, 'duration', new)
    text_child(note, 'type', TYPES[str(denominator)])
    for dot in note.findall('dot'):
        note.remove(dot)
    for _ in range(dots):
        ET.SubElement(note, 'dot')


def apply_edit(tree, selected, action, value):
    if action == 'prepare':
        return
    if action == 'title':
        title = str(value or 'Untitled score').strip()[:120]
        work = tree.getroot().find('work')
        if work is None:
            work = ET.SubElement(tree.getroot(), 'work')
        text_child(work, 'work-title', title)
        text_child(tree.getroot(), 'movement-title', title)
        return
    selected = set(selected)
    nodes = [(measure, note) for measure in tree.findall('.//measure') for note in measure.findall('note') if note.get('id') in selected]
    if not nodes or len(nodes) != len(selected):
        raise PipelineError('Chọn nốt hoặc dấu lặng trên phổ trước khi chỉnh sửa.')
    if action in {'slur', 'tie'}:
        if len(nodes) < 2:
            raise PipelineError('Chọn ít nhất hai nốt để nối (Shift + nhấp hoặc kéo vùng chọn).')
        first, last = nodes[0][1], nodes[-1][1]
        if any(pitch_value(note) is None for _, note in nodes):
            raise PipelineError('Không nối dấu lặng.')
        if action == 'tie' and len({pitch_value(note) for _, note in nodes}) != 1:
            raise PipelineError('Dấu nối chỉ dùng cho các nốt cùng cao độ.')
        tag = 'slur' if action == 'slur' else 'tied'
        endpoints = ((first, 'start'), (last, 'stop'))
        removing = all(note.find(f"notations/{tag}[@type='{kind}']") is not None for note, kind in endpoints)
        for note, kind in endpoints:
            notations = note.find('notations')
            if notations is None:
                notations = ET.SubElement(note, 'notations')
            if removing:
                for child in notations.findall(f"{tag}[@type='{kind}']"):
                    notations.remove(child)
                if action == 'tie':
                    for child in note.findall(f"tie[@type='{kind}']"):
                        note.remove(child)
                continue
            ET.SubElement(notations, tag, type=kind, number='1')
            if action == 'tie':
                ET.SubElement(note, 'tie', type=kind)
        return
    divisions = int(tree.findtext('.//attributes/divisions', '16'))
    if action in {'duration', 'dot', 'insert'}:
        # 512th notes with a dot require at least 256 divisions per quarter.
        divisions = normalize_resolution(tree, 256)
    for measure, note in nodes:
        pitch = pitch_value(note)
        if action == 'duration':
            if str(value) not in DURATIONS:
                raise PipelineError('Trường độ không hợp lệ.')
            set_duration(measure, note, divisions, value, len(note.findall('dot')))
        elif action == 'dot':
            denominator = next((key for key, kind in TYPES.items() if kind == note.findtext('type')), '4')
            set_duration(measure, note, divisions, denominator, 0 if note.findall('dot') else 1)
        elif action in {'transpose', 'pitch', 'insert'}:
            if action == 'insert' and pitch is None:
                set_duration(measure, note, divisions, '4')
            target = int(value) if action in {'pitch', 'insert'} else (pitch if pitch is not None else 60) + int(value)
            set_pitch(note, target)
        elif action == 'accidental':
            if pitch is None:
                continue
            target = note.find('pitch')
            alter = {'flat': -1, 'natural': 0, 'sharp': 1, 'double-flat': -2, 'double-sharp': 2, 'sharp-sharp': 2}.get(str(value))
            if alter is None:
                raise PipelineError('Dấu hóa không hợp lệ.')
            text_child(target, 'alter', alter)
            text_child(note, 'accidental', 'flat-flat' if value == 'double-flat' else value)
            if not 21 <= pitch_value(note) <= 108:
                raise PipelineError('Cao độ vượt dải piano.')
        elif action == 'grace':
            denominator, _, slash = str(value).partition(':')
            if denominator not in DURATIONS or float(denominator) < 8 or slash not in {'yes', 'no'}:
                raise PipelineError('Nốt hoa mỹ không hợp lệ.')
            if pitch is None:
                raise PipelineError('Chọn một nốt nhạc để thêm nốt hoa mỹ trước nó.')
            if note.find('grace') is not None:
                if note.find('grace').get('slash', 'no') == slash and note.findtext('type') == TYPES[denominator]:
                    measure.remove(note)
                    continue
                note.find('grace').set('slash', slash)
                text_child(note, 'type', TYPES[denominator])
                continue
            siblings = list(measure)
            position = siblings.index(note)
            previous = siblings[position - 1] if position else None
            if previous is not None and previous.find('grace') is not None and pitch_value(previous) == pitch and previous.findtext('voice', '1') == note.findtext('voice', '1'):
                if previous.find('grace').get('slash', 'no') == slash and previous.findtext('type') == TYPES[denominator]:
                    measure.remove(previous)
                else:
                    previous.find('grace').set('slash', slash)
                    text_child(previous, 'type', TYPES[denominator])
                continue
            grace = ET.Element('note', id='grace-' + uuid.uuid4().hex[:12])
            ET.SubElement(grace, 'grace', slash=slash)
            grace.append(copy.deepcopy(note.find('pitch')))
            text_child(grace, 'voice', note.findtext('voice', '1'))
            text_child(grace, 'type', TYPES[denominator])
            text_child(grace, 'staff', note.findtext('staff', '1'))
            measure.insert(list(measure).index(note), grace)
        elif action in {'rest', 'delete'}:
            if action == 'rest' and value == 'note':
                set_pitch(note, 60)
                continue
            if note.find('grace') is not None:
                measure.remove(note)
                continue
            siblings = list(measure)
            position = siblings.index(note)
            if note.find('chord') is not None:
                measure.remove(note)
                continue
            if position + 1 < len(siblings) and siblings[position + 1].tag == 'note' and siblings[position + 1].find('chord') is not None:
                following = siblings[position + 1]
                following.remove(following.find('chord'))
                measure.remove(note)
                continue
            for child in note.findall('pitch') + note.findall('accidental') + note.findall('tie') + note.findall('notations'):
                note.remove(child)
            if note.find('rest') is None:
                note.insert(0, ET.Element('rest'))
        elif action == 'voice':
            if str(value) not in {str(voice) for voice in range(1, 9)}:
                raise PipelineError('Bè phải là 1–8.')
            text_child(note, 'voice', value)
        elif action == 'articulation':
            if value not in {'staccato', 'tenuto', 'accent', 'strong-accent'}:
                raise PipelineError('Ký hiệu không hợp lệ.')
            notations = note.find('notations')
            if notations is None:
                notations = ET.SubElement(note, 'notations')
            articulations = notations.find('articulations')
            if articulations is None:
                articulations = ET.SubElement(notations, 'articulations')
            existing = articulations.find(str(value))
            if existing is not None:
                articulations.remove(existing)
            else:
                ET.SubElement(articulations, str(value))
        else:
            raise PipelineError('Thao tác chỉnh sửa không hỗ trợ.')


def export_revision(folder: Path, source: dict, update, cancelled):
    import pretty_midi
    import verovio
    from .pipeline import engrave
    pages, timeline = engrave(folder, update, cancelled)
    toolkit = verovio.toolkit(False)
    toolkit.setResourcePath(str(Path(verovio.__file__).parent / 'data'))
    if not toolkit.loadFile(str(folder / 'piano.musicxml')):
        raise PipelineError('Không đọc được phổ sau khi sửa.')
    midi_bytes = base64.b64decode(toolkit.renderToMIDI())
    tree = ET.parse(folder / 'piano.musicxml')
    if any(note.findtext('type') in {'64th', '128th', '256th', '512th'} for note in tree.findall('.//note')):
        midi_bytes = precise_midi(toolkit, tree, midi_bytes)
    (folder / 'piano.mid').write_bytes(midi_bytes)
    midi = pretty_midi.PrettyMIDI(str(folder / 'piano.mid'))
    notes = sorted([{'id': f't{track}-n{index}', 'pitch': note.pitch, 'start': note.start, 'end': note.end,
                     'velocity': note.velocity, 'hand': 'L' if note.pitch < 60 else 'R'}
                    for track, instrument in enumerate(midi.instruments) if not instrument.is_drum
                    for index, note in enumerate(instrument.notes) if 21 <= note.pitch <= 108], key=lambda note: note['start'])
    (folder / 'piano_notes.json').write_text(json.dumps(notes), encoding='utf-8')
    result = {**source, 'pages': pages, 'timeline': timeline, 'notes': notes, 'editable': True,
              'originalAudio': None, 'duration': max(float(source.get('duration', 0)), midi.get_end_time()),
              'downloads': {'midi': 'piano.mid', 'musicxml': 'piano.musicxml', 'notes': 'piano_notes.json'}}
    result['title'] = ET.parse(folder / 'piano.musicxml').findtext('work/work-title', source['title'])
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    return result


def precise_midi(toolkit, tree, data):
    """Verovio's 120 PPQ export truncates very short notes. Rebuild at 15360 PPQ."""
    import io
    import mido
    midi = mido.MidiFile(file=io.BytesIO(data))
    factor = 15360 // midi.ticks_per_beat
    tempo_points = [(0.0, 0, 500000)]
    elapsed, absolute, tempo = 0.0, 0, 500000
    for message in mido.merge_tracks(midi.tracks):
        elapsed += mido.tick2second(message.time, midi.ticks_per_beat, tempo)
        absolute += message.time * factor
        if message.type == 'set_tempo':
            tempo = message.tempo
            tempo_points.append((elapsed, absolute, tempo))

    def ticks(milliseconds):
        seconds = milliseconds / 1000
        start, tick, tempo = next(point for point in reversed(tempo_points) if point[0] <= seconds)
        return tick + round(mido.second2tick(seconds - start, 15360, tempo))

    midi.ticks_per_beat = 15360
    events = []
    for track in midi.tracks:
        absolute = 0
        metadata = []
        for message in track:
            absolute += message.time * factor
            if message.type not in {'note_on', 'note_off', 'end_of_track'}:
                metadata.append((absolute, message.copy()))
        events.append(metadata)
    for index, part in enumerate(tree.findall('.//part')):
        target = min(index + 1, len(events) - 1)
        channel = next((message.channel for _, message in events[target] if message.type == 'program_change'), 0)
        sounding = []
        ties = {}
        for note in part.findall('.//note'):
            if note.find('rest') is not None:
                continue
            values = toolkit.getMIDIValuesForElement(note.get('id'))
            if not values or values.get('duration', 0) <= 0:
                continue
            start = ticks(values['time'])
            end = max(start + 1, ticks(values['time'] + values['duration']))
            key = (note.findtext('voice', '1'), note.findtext('staff', '1'), values['pitch'])
            tie_types = {tie.get('type') for tie in note.findall('tie')}
            if 'stop' in tie_types and key in ties:
                event = ties[key]
                event[1] = max(event[1], end)
            else:
                event = [start, end, values['pitch']]
                sounding.append(event)
            if 'start' in tie_types:
                ties[key] = event
            else:
                ties.pop(key, None)
        for start, end, pitch in sounding:
            events[target].extend(((start, mido.Message('note_on', note=pitch, velocity=90, channel=channel)),
                                   (end, mido.Message('note_off', note=pitch, velocity=0, channel=channel))))
    for track, entries in zip(midi.tracks, events):
        track.clear()
        previous = 0
        for position, message in sorted(entries, key=lambda event: (event[0], event[1].type != 'note_off')):
            track.append(message.copy(time=position - previous))
            previous = position
    output = io.BytesIO()
    midi.save(file=output)
    return output.getvalue()
