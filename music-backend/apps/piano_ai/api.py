"""Run: python -m uvicorn apps.piano_ai.api:app --host 127.0.0.1 --port 8001"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .pipeline import Cancelled, PipelineError, convert, preflight, youtube_url
from .transcriber import selected_device

BASE = Path(__file__).resolve().parents[2]
load_dotenv(BASE / '.env')
ROOT = Path(os.environ.get('PIANO_JOBS_DIR', str(BASE / 'media' / 'piano_jobs'))).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
MAX_BYTES = int(os.environ.get('PIANO_MAX_UPLOAD_MB', '100')) * 1024 * 1024
EXTENSIONS = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.mp4', '.webm', '.mid', '.midi'}
POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix='piano-ai')
SLOTS = threading.BoundedSemaphore(3)
LOCK = threading.Lock()
EVENTS: dict[str, threading.Event] = {}

app = FastAPI(title='Piano AI', version='1.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('PIANO_CORS_ORIGINS', 'http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082,null').split(','),
    # Expo Go's embedded DOM uses a local file origin; physical phones use a LAN origin.
    allow_origin_regex=os.environ.get('PIANO_CORS_ORIGIN_REGEX',
        r'https?://(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?::\d+)?'),
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type'],
)


def folder_for(job_id: str) -> Path:
    try:
        if str(uuid.UUID(job_id)) != job_id:
            raise ValueError()
    except ValueError:
        raise HTTPException(404, 'Không tìm thấy tác vụ.') from None
    folder = ROOT / job_id
    if not (folder / 'status.json').is_file():
        raise HTTPException(404, 'Không tìm thấy tác vụ.')
    return folder


def write_status(folder: Path, stage: str, progress: int, message: str, timings: dict | None = None):
    # Atomic replacement: polling never observes a partially written JSON file.
    with LOCK:
        temporary = folder / 'status.tmp'
        payload = {'id': folder.name, 'status': stage, 'progress': progress, 'message': message}
        if timings is not None:
            payload['timings'] = timings
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
        temporary.replace(folder / 'status.json')


def read_status(folder: Path):
    # Windows does not allow replacing a file while another thread has it open.
    with LOCK:
        return json.loads((folder / 'status.json').read_text(encoding='utf-8'))


def work(folder: Path, source: str, title: str, cancelled: threading.Event):
    started = time.perf_counter()
    stage_started = started
    current_stage = 'queued'
    stage_seconds: dict[str, float] = {}

    def update(stage: str, progress: int, message: str):
        nonlocal current_stage, stage_started
        now = time.perf_counter()
        if stage != current_stage:
            stage_seconds[current_stage] = stage_seconds.get(current_stage, 0.0) + now - stage_started
            current_stage = stage
            stage_started = now
        timings = {
            'elapsedSeconds': round(now - started, 2),
            'stagesSeconds': {name: round(seconds, 2) for name, seconds in stage_seconds.items()},
        }
        write_status(folder, stage, progress, message, timings)

    try:
        convert(folder, source, title, update, cancelled)
        if cancelled.is_set():
            raise Cancelled('Đã hủy chuyển nhạc.')
        update('completed', 100, 'Đã chuyển thành piano và phổ nhạc.')
    except Cancelled:
        update('cancelled', 0, 'Đã hủy chuyển nhạc.')
    except Exception as exc:
        # Full trace stays on the server. Do not return paths or HF credentials.
        import traceback
        token = os.environ.get('HF_TOKEN', '')
        details = traceback.format_exc()
        if token:
            details = details.replace(token, '[REDACTED]')
        (folder / 'error.log').write_text(details, encoding='utf-8')
        message = str(exc) if isinstance(exc, PipelineError) else 'Không chuyển được bản nhạc. Xem error.log trên máy chủ.'
        message = re.sub(r'hf_[A-Za-z0-9]+', '[REDACTED]', message)
        update('failed', 0, message)
    finally:
        finished = time.perf_counter()
        stage_seconds[current_stage] = stage_seconds.get(current_stage, 0.0) + finished - stage_started
        (folder / 'timings.json').write_text(json.dumps({
            'elapsedSeconds': round(finished - started, 2),
            'stagesSeconds': {name: round(seconds, 2) for name, seconds in stage_seconds.items()},
        }, ensure_ascii=False), encoding='utf-8')
        with LOCK:
            EVENTS.pop(folder.name, None)
        SLOTS.release()


# Interrupted jobs are never silently reported as still running after a restart.
for status_path in ROOT.glob('*/status.json'):
    try:
        old = json.loads(status_path.read_text(encoding='utf-8'))
        if old['status'] not in {'completed', 'failed', 'cancelled'}:
            write_status(status_path.parent, 'failed', 0, 'Dịch vụ đã khởi động lại. Vui lòng gửi lại bản nhạc.')
    except (OSError, ValueError, KeyError):
        pass


@app.get('/health')
def health():
    missing = preflight()
    try:
        import torch
        accelerator = {
            'torch': torch.__version__,
            'cudaAvailable': torch.cuda.is_available(),
            'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except ImportError:
        accelerator = {'torch': None, 'cudaAvailable': False, 'gpu': None}
    return {'status': 'ready' if not missing else 'setup_required', 'missing': missing,
            'device': os.environ.get('PIANO_AI_DEVICE', 'auto'),
            'effectiveDevice': selected_device() if accelerator['torch'] else 'unavailable',
            'accelerator': accelerator,
            'maxUploadMB': MAX_BYTES // (1024 * 1024)}


@app.post('/jobs', status_code=202)
async def create_job(file: UploadFile | None = File(default=None), youtube: str = Form(default='')):
    if bool(file) == bool(youtube.strip()):
        raise HTTPException(400, 'Chọn một file hoặc nhập một link YouTube.')
    if file and Path(file.filename or '').suffix.lower() not in EXTENSIONS:
        raise HTTPException(400, 'Định dạng không hỗ trợ. Chọn audio, video hoặc MIDI.')
    try:
        source = youtube_url(youtube) if youtube.strip() else ''
    except (PipelineError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from None
    missing = preflight()
    if missing:
        raise HTTPException(503, 'Dịch vụ AI chưa cài đủ thư viện: ' + ', '.join(missing))
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Hàng đợi đang đầy. Hãy thử lại khi tác vụ trước hoàn tất.')
    folder = ROOT / str(uuid.uuid4())
    folder.mkdir()
    submitted = False
    try:
        title = 'YouTube Piano'
        if file:
            title = Path(file.filename or 'Piano').stem[:120]
            target = folder / ('source' + Path(file.filename or '').suffix.lower())
            size = 0
            with target.open('wb') as output:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise HTTPException(413, f'File vượt giới hạn {MAX_BYTES // (1024 * 1024)} MB.')
                    output.write(chunk)
            if not size:
                raise HTTPException(400, 'File trống.')
            source = str(target)
        write_status(folder, 'queued', 0, 'Đã nhận bản nhạc, đang chờ xử lý…')
        cancelled = threading.Event()
        with LOCK:
            EVENTS[folder.name] = cancelled
        POOL.submit(work, folder, source, title, cancelled)
        submitted = True
        return read_status(folder)
    finally:
        if file:
            await file.close()
        if not submitted:
            SLOTS.release()
            # Only remove the newly created upload, never a user path.
            for path in folder.iterdir():
                if path.is_file():
                    path.unlink()
            folder.rmdir()


@app.get('/jobs/{job_id}')
def status(job_id: str):
    return read_status(folder_for(job_id))


@app.post('/jobs/{job_id}/cancel')
def cancel(job_id: str):
    folder_for(job_id)
    with LOCK:
        event = EVENTS.get(job_id)
        if event:
            event.set()
    return {'id': job_id, 'cancellationRequested': event is not None}


@app.get('/jobs/{job_id}/result')
def result(job_id: str):
    folder = folder_for(job_id)
    state = read_status(folder)
    if state['status'] != 'completed':
        raise HTTPException(409, 'Bản nhạc chưa xử lý thành công.')
    return json.loads((folder / 'result.json').read_text(encoding='utf-8'))


@app.get('/jobs/{job_id}/assets/{filename}')
def asset(job_id: str, filename: str):
    folder = folder_for(job_id)
    if read_status(folder)['status'] != 'completed':
        raise HTTPException(409, 'Bản nhạc chưa sẵn sàng.')
    allowed = {'piano.mid', 'piano.musicxml', 'piano_notes.json', 'original.mp3', 'editor.json'}
    if filename not in allowed and not re.fullmatch(r'score-[1-9]\d*\.svg', filename):
        raise HTTPException(404, 'Không tìm thấy tệp.')
    path = folder / filename
    if not path.is_file():
        raise HTTPException(404, 'Không tìm thấy tệp.')
    media = {'svg': 'image/svg+xml', 'mp3': 'audio/mpeg', 'mid': 'audio/midi',
             'musicxml': 'application/vnd.recordare.musicxml+xml', 'json': 'application/json'}
    response = FileResponse(path, media_type=media[path.suffix[1:]],
                            filename=filename if path.suffix in {'.mid', '.musicxml', '.json'} else None)
    response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'unsafe-inline'"
    return response


class ScoreEdit(BaseModel):
    selected: list[str] = Field(default_factory=list, max_length=1000)
    action: str = Field(max_length=30)
    value: str | int | float | None = None


class NewScore(BaseModel):
    title: str = Field(default='Untitled score', max_length=120)
    bpm: float = Field(default=100, ge=35, le=240)
    bars: int = Field(default=8, ge=1, le=64)


EDIT_LOCK = threading.Lock()


@app.post('/jobs/{job_id}/edit')
def edit_score(job_id: str, request: ScoreEdit):
    from .edition import identify_score, apply_edit, export_revision
    import shutil
    source_folder = folder_for(job_id)
    if read_status(source_folder)['status'] != 'completed':
        raise HTTPException(409, 'Bản nhạc chưa sẵn sàng.')
    if not EDIT_LOCK.acquire(blocking=False):
        raise HTTPException(409, 'Đang lưu thay đổi trước. Vui lòng thử lại.')
    folder = ROOT / str(uuid.uuid4())
    folder.mkdir()
    try:
        source = json.loads((source_folder / 'result.json').read_text(encoding='utf-8'))
        shutil.copyfile(source_folder / 'piano.musicxml', folder / 'piano.musicxml')
        tree = identify_score(folder / 'piano.musicxml')
        apply_edit(tree, request.selected, request.action, request.value)
        tree.write(folder / 'piano.musicxml', encoding='utf-8', xml_declaration=True)
        write_status(folder, 'engraving', 80, 'Đang lưu và dựng lại phổ…')
        result = export_revision(folder, source, lambda *args: None, threading.Event())
        write_status(folder, 'completed', 100, 'Đã lưu phiên bản mới.')
        return {'id': folder.name, **result}
    except (PipelineError, ValueError) as exc:
        write_status(folder, 'failed', 0, 'Không lưu được thay đổi.')
        raise HTTPException(400, str(exc)) from None
    finally:
        EDIT_LOCK.release()


@app.post('/scores', status_code=201)
def create_score(request: NewScore):
    from .score_engine import PianoScoreSettings, build_musicxml
    from .edition import export_revision
    folder = ROOT / str(uuid.uuid4())
    folder.mkdir()
    duration = request.bars * 4 * 60 / request.bpm
    options = PianoScoreSettings(bpm=request.bpm, full_audio_seconds=duration, chord_symbols=False)
    build_musicxml([], options, request.bpm, 0, request.title, folder / 'piano.musicxml')
    source = {'title': request.title, 'duration': duration, 'bpm': request.bpm, 'meter': '4/4',
              'key': 'C major', 'notice': '', 'originalAudio': None}
    write_status(folder, 'engraving', 80, 'Đang tạo bản nhạc…')
    result = export_revision(folder, source, lambda *args: None, threading.Event())
    write_status(folder, 'completed', 100, 'Đã tạo bản nhạc.')
    return {'id': folder.name, **result}
