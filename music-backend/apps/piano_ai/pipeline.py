"""The notebook's pipeline, without Kaggle-only widgets, apt, or notebook globals."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlparse


class PipelineError(Exception):
    pass


class Cancelled(PipelineError):
    pass


def youtube_url(value: str) -> str:
    """Only accept a video ID on an exact YouTube hostname, never arbitrary URLs."""
    parsed = urlparse(value.strip())
    if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password or parsed.port:
        raise PipelineError('Link phải là địa chỉ video YouTube hợp lệ.')
    host = (parsed.hostname or '').lower()
    if host in {'youtu.be', 'www.youtu.be'}:
        video_id = parsed.path.strip('/')
    elif host in {'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'}:
        if parsed.path == '/watch':
            video_id = parse_qs(parsed.query).get('v', [''])[0]
        else:
            match = re.fullmatch(r'/(?:shorts|embed|live)/([\w-]+)', parsed.path)
            video_id = match[1] if match else ''
    else:
        video_id = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
        raise PipelineError('Vui lòng nhập link một video YouTube, không phải playlist.')
    return f'https://www.youtube.com/watch?v={video_id}'


def run_command(args: list[str], folder: Path, cancelled: threading.Event, timeout: int = 7200):
    """Keep subprocess output private; never put credentials or full logs in API responses."""
    import time
    if cancelled.is_set():
        raise Cancelled('Đã hủy chuyển nhạc.')
    with (folder / 'worker.log').open('ab') as log:
        environment = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'NO_COLOR': '1'}
        process = subprocess.Popen(args, stdout=log, stderr=log, cwd=folder, env=environment)
        started = time.monotonic()
        try:
            while process.poll() is None:
                if cancelled.wait(0.2):
                    raise Cancelled('Đã hủy chuyển nhạc.')
                if time.monotonic() - started > timeout:
                    raise PipelineError('Xử lý quá thời gian cho phép. Hãy thử file ngắn hơn.')
            if process.returncode:
                raise PipelineError('Lệnh xử lý thất bại. Chi tiết nằm trong worker.log trên máy chủ.')
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def ffmpeg_binary() -> str:
    binary = os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
    if binary:
        return binary
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def preflight() -> list[str]:
    packages = ('torch', 'muscriptor', 'pretty_midi', 'verovio', 'librosa', 'soundfile', 'yt_dlp', 'imageio_ffmpeg')
    return [name for name in packages if importlib.util.find_spec(name) is None]


def engrave(folder: Path, update, cancelled):
    import verovio
    from .edition import identify_score, editor_data
    tree = identify_score(folder / 'piano.musicxml')
    (folder / 'editor.json').write_text(json.dumps(editor_data(tree)), encoding='utf-8')
    toolkit = verovio.toolkit(False)
    toolkit.setResourcePath(str(Path(verovio.__file__).parent / 'data'))
    toolkit.setOptions({
        'pageWidth': 2970, 'pageHeight': 2100, 'scale': 60,
        'pageMarginLeft': 90, 'pageMarginRight': 90,
        'pageMarginTop': 80, 'pageMarginBottom': 80,
        'spacingLinear': 0.36, 'spacingNonLinear': 0.68,
        'spacingStaff': 17, 'spacingSystem': 16, 'systemMaxPerPage': 3,
        'breaks': 'auto',
    })
    if not toolkit.loadFile(str(folder / 'piano.musicxml')):
        raise PipelineError('Không dựng được phổ nhạc từ MusicXML.')
    count = toolkit.getPageCount()
    if not count:
        raise PipelineError('Phổ nhạc không có trang nào.')
    pages = []
    for page in range(1, count + 1):
        if cancelled.is_set():
            raise Cancelled('Đã hủy chuyển nhạc.')
        name = f'score-{page}.svg'
        (folder / name).write_text(toolkit.renderToSVG(page), encoding='utf-8')
        pages.append(name)
        update('engraving', 80 + int(15 * page / count), f'Đang dựng trang phổ {page}/{count}…')
    # IDs are those in the rendered SVGs. Timemap timestamps are milliseconds.
    timemap = toolkit.renderToTimemap()
    if isinstance(timemap, str):
        timemap = json.loads(timemap)
    timeline = []
    for event in timemap:
        on = event.get('on', [])
        timeline.append({
            'time': float(event.get('tstamp', 0)) / 1000,
            'on': on, 'off': event.get('off', []),
            'page': toolkit.getPageWithElement(on[0]) if on else None,
        })
    return pages, timeline


def convert(folder: Path, source: str, title: str, update, cancelled: threading.Event) -> dict:
    import numpy as np
    import pretty_midi
    import soundfile as sf
    from .analysis import estimate_meter, estimate_tempo_audio
    from .score_engine import DIVISIONS, PianoScoreSettings, create_piano_score

    max_seconds = int(os.environ.get('PIANO_MAX_SECONDS', '1200'))
    missing = preflight()
    if missing:
        raise PipelineError('Thiếu thư viện AI: ' + ', '.join(missing))
    original = None
    input_path = Path(source)
    if source.startswith('https://'):
        update('downloading', 8, 'Đang tải âm thanh YouTube…')
        run_command([
            sys.executable, '-m', 'yt_dlp', '--ignore-config', '--no-playlist',
            '--socket-timeout', '30', '--retries', '2', '--max-filesize', '100M',
            '--match-filter', f'duration <= {max_seconds} & !is_live',
            '-f', 'bestaudio/best', '--write-info-json',
            '-o', str(folder / 'youtube.%(ext)s'), youtube_url(source),
        ], folder, cancelled, timeout=600)
        inputs = [path for path in folder.glob('youtube.*') if path.suffix != '.json' and not path.name.endswith('.part')]
        if len(inputs) != 1:
            raise PipelineError('Không tải được video. Video có thể quá dài, bị hạn chế hoặc yêu cầu đăng nhập.')
        input_path = inputs[0]
        info = folder / 'youtube.info.json'
        if info.exists():
            title = str(json.loads(info.read_text(encoding='utf-8')).get('title', title))[:120]

    midi_path = folder / 'song.mid'
    if input_path.suffix.lower() in {'.mid', '.midi'}:
        update('analyzing', 65, 'Đang đọc MIDI và dựng phổ piano…')
        shutil.copyfile(input_path, midi_path)
        duration = pretty_midi.PrettyMIDI(str(midi_path)).get_end_time()
    else:
        update('preparing', 18, 'Đang chuẩn hóa âm thanh…')
        wav = folder / 'input.wav'
        ffmpeg = ffmpeg_binary()
        run_command([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(input_path),
                     '-t', str(max_seconds + 1), '-vn', '-ac', '1', '-ar', '16000', str(wav)], folder, cancelled, 600)
        duration = sf.info(str(wav)).duration
        if not 0 < duration <= max_seconds:
            raise PipelineError(f'Âm thanh phải dài từ 1 giây đến {max_seconds // 60} phút.')
        original = 'original.mp3'
        run_command([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav),
                     '-codec:a', 'libmp3lame', '-b:a', '128k', str(folder / original)], folder, cancelled, 600)
        from .transcriber import transcribe
        transcribe(wav, midi_path, update, cancelled)
    if cancelled.is_set():
        raise Cancelled('Đã hủy chuyển nhạc.')
    if duration > max_seconds:
        raise PipelineError('Bản nhạc vượt thời lượng cho phép.')
    update('analyzing', 68, 'Đang phân tích nhịp, giọng và chia hai tay piano…')
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    if not any(instrument.notes for instrument in midi.instruments if not instrument.is_drum):
        raise PipelineError('AI chưa nhận diện được nốt nhạc trong file này. Hãy thử một đoạn có tiếng đàn rõ hơn.')
    _, tempos = midi.get_tempo_changes()
    recorded = [float(value) for value in tempos if 35 <= value <= 240]
    bpm = float(np.median(recorded)) if recorded else 120.0
    reliable = bool(recorded and (len(recorded) > 1 or abs(bpm - 120) > 0.2))
    tempo_source = 'MIDI tempo'
    if original and not reliable:
        estimated, tempo_source, _ = estimate_tempo_audio(folder / 'input.wav', duration, bpm, reliable)
        bpm = estimated or bpm
    meter, meter_source = estimate_meter(midi, bpm)
    options = PianoScoreSettings(bpm=bpm, time_signature=meter, full_audio_seconds=duration,
                                 tempo_source=tempo_source, meter_source=meter_source)
    diagnostics = create_piano_score(midi_path, folder, options, title=title)
    rows = json.loads((folder / 'piano_notes.json').read_text(encoding='utf-8'))
    notes = [{
        'id': row['id'], 'pitch': row['pitch'], 'velocity': row['velocity'], 'hand': row['hand'],
        'start': row['start'] / DIVISIONS * 60 / bpm,
        'end': row['end'] / DIVISIONS * 60 / bpm,
    } for row in rows if 21 <= row['pitch'] <= 108]
    if not notes:
        raise PipelineError('Không nhận diện được nốt nào trong dải piano A0–C8.')
    pages, timeline = engrave(folder, update, cancelled)
    result = {
        'editable': True,
        'title': title, 'duration': max(duration, max(note['end'] for note in notes)),
        'bpm': bpm, 'meter': meter, 'key': diagnostics['key_source'], 'notes': notes,
        'pages': pages, 'timeline': timeline, 'originalAudio': original,
        'downloads': {'midi': 'piano.mid', 'musicxml': 'piano.musicxml', 'notes': 'piano_notes.json'},
        'notice': 'Phổ nhạc do AI ước lượng; nhịp, hợp âm hoặc một số nốt có thể khác bản gốc.',
    }
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    return result
