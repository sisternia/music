import { useCallback, useEffect, useRef, useState } from 'react';
import { pianoRequest, songAsset, type PianoSong } from './transcription';

export type EditableNote = { id: string; pitch: number | null; rest: boolean; duration: string; dots: number; voice: string; staff: string; measure: string; accidental?: string; grace?: string; articulations?: string[]; slur?: boolean; tie?: boolean };

export function useScoreEditor(song: PianoSong, enabled: boolean, onChange: (song: PianoSong) => void, pause: () => void) {
  const [notes, setNotes] = useState<EditableNote[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [past, setPast] = useState<PianoSong[]>([]);
  const [future, setFuture] = useState<PianoSong[]>([]);
  const latest = useRef({ onChange, pause });
  useEffect(() => { latest.current = { onChange, pause }; }, [onChange, pause]);

  useEffect(() => {
    if (!enabled) return;
    const controller = new AbortController();
    const load = async () => {
      try {
        if (!song.editable) {
          const prepared = await pianoRequest<PianoSong>(`/jobs/${song.id}/edit`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'prepare' }), signal: controller.signal });
          if (!controller.signal.aborted) latest.current.onChange(prepared);
          return;
        }
        const response = await fetch(songAsset(song, 'editor.json'), { signal: controller.signal });
        if (!response.ok) throw new Error('Không đọc được dữ liệu chỉnh sửa. Hãy thử mở lại Edition.');
        const rows: EditableNote[] = await response.json();
        if (!controller.signal.aborted) {
          setNotes(rows); setError('');
          setSelected(current => current.filter(id => rows.some(note => note.id === id)));
        }
      } catch (reason) {
        if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : 'Không mở được trình chỉnh sửa.');
      }
    };
    void load();
    return () => controller.abort();
  }, [enabled, song]);

  const apply = useCallback(async (action: string, value?: string | number) => {
    if (busy) return;
    if (!selected.length && action !== 'title') { setError('Chọn nốt hoặc dấu lặng trên phổ trước. Shift + nhấp để chọn nhiều nốt.'); return; }
    latest.current.pause(); setBusy(true); setError('');
    try {
      const updated = await pianoRequest<PianoSong>(`/jobs/${song.id}/edit`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selected, action, value }) });
      setPast(history => [...history, song].slice(-20)); setFuture([]);
      latest.current.onChange(updated);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Không lưu được thay đổi.'); }
    finally { setBusy(false); }
  }, [busy, selected, song]);
  const undo = useCallback(() => {
    if (!past.length || busy) return;
    latest.current.pause();
    setFuture(history => [song, ...history]);
    latest.current.onChange(past[past.length - 1]);
    setPast(history => history.slice(0, -1)); setError('');
  }, [past, busy, song]);
  const redo = useCallback(() => {
    if (!future.length || busy) return;
    latest.current.pause();
    setPast(history => [...history, song]);
    latest.current.onChange(future[0]); setFuture(history => history.slice(1)); setError('');
  }, [future, busy, song]);
  return { notes, selected, setSelected, busy, error, apply, undo, redo, canUndo: !!past.length, canRedo: !!future.length };
}
