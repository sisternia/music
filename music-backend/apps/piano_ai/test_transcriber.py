from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from muscriptor.events import ProgressEvent

from .pipeline import Cancelled
from . import transcriber


class StubModel:
    def __init__(self):
        self.calls = 0

    def detect_beat_grid_for(self, audio, mode):
        return None

    def transcribe(self, audio):
        self.calls += 1
        yield ProgressEvent(0, 2)
        yield ProgressEvent(1, 2)
        yield ProgressEvent(2, 2)

    def events_to_midi_bytes(self, events, beat_grid):
        list(events)
        return b'MThd'


class TranscriberTests(unittest.TestCase):
    def test_progress_and_cancellation(self):
        model = StubModel()
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(transcriber, '_get_model', return_value=model), \
                patch.object(transcriber, 'selected_device', return_value='cpu'):
            path = Path(directory) / 'song.mid'
            updates = []
            cancelled = threading.Event()

            def update(stage, progress, message):
                updates.append(progress)

            transcriber.transcribe(Path(directory) / 'input.wav', path, update, cancelled)
            self.assertEqual(path.read_bytes(), b'MThd')
            self.assertEqual(updates, [30, 32, 33, 49, 66])

            path.unlink()

            def cancel_after_chunk(stage, progress, message):
                if progress == 49:
                    cancelled.set()

            with self.assertRaises(Cancelled):
                transcriber.transcribe(Path(directory) / 'input.wav', path,
                                       cancel_after_chunk, cancelled)
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
