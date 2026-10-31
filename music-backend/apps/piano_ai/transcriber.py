"""Keep the small MuScriptor model warm across the service's sequential jobs."""
from __future__ import annotations

import os
from pathlib import Path
import threading
import time

from .pipeline import Cancelled, PipelineError


_model = None
_model_device: str | None = None
_model_lock = threading.Lock()


def selected_device() -> str:
    configured = os.environ.get('PIANO_AI_DEVICE', 'auto').strip() or 'auto'
    if configured != 'auto':
        return configured
    import torch
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def _get_model(device: str):
    global _model, _model_device
    with _model_lock:
        if _model is None or _model_device != device:
            from muscriptor.transcription_model import TranscriptionModel
            _model = TranscriptionModel.load_model(weights_path='small', device=device)
            _model_device = device
        return _model


def transcribe(wav: Path, midi: Path, update, cancelled: threading.Event) -> None:
    """Use the CLI's default decoding and beat alignment, with chunk progress."""
    from muscriptor.events import ProgressEvent

    timeout = int(os.environ.get('PIANO_JOB_TIMEOUT', '7200'))
    deadline = time.monotonic() + timeout

    def check():
        if cancelled.is_set():
            raise Cancelled('Đã hủy chuyển nhạc.')
        if time.monotonic() > deadline:
            raise PipelineError('Xử lý quá thời gian cho phép. Hãy thử file ngắn hơn.')

    check()
    device = selected_device()
    update('transcribing', 30, f'Đang nạp mô hình AI trên {device.upper()}…')
    model = _get_model(device)
    check()
    update('transcribing', 32, 'Đang phân tích nhịp và chuyển âm thanh thành MIDI…')
    beat_grid = model.detect_beat_grid_for(wav, 'best-effort')
    check()

    def events():
        for event in model.transcribe(wav):
            check()
            if isinstance(event, ProgressEvent) and event.total:
                progress = 33 + int(33 * event.completed / event.total)
                update('transcribing', progress,
                       f'AI đã xử lý {event.completed}/{event.total} đoạn nhạc trên {device.upper()}…')
            yield event

    data = model.events_to_midi_bytes(events(), beat_grid=beat_grid)
    check()
    midi.write_bytes(data)
