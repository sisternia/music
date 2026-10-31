import { useEffect, useRef, useState } from 'react';
import { pianoRequest, type PianoSong, type TranscriptionJob } from '../hooks/transcription';

type Props = { open: boolean; embedded?: boolean; onClose: () => void; onImported: (song: PianoSong) => void };

export default function PianoImport({ open, embedded = false, onClose, onImported }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [youtube, setYoutube] = useState('');
  const [job, setJob] = useState<TranscriptionJob | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const fileInput = useRef<HTMLInputElement>(null);
  const imported = useRef(onImported);
  const close = useRef(onClose);
  useEffect(() => { imported.current = onImported; close.current = onClose; }, [onImported, onClose]);
  const busy = submitting || !!job && !['completed', 'failed', 'cancelled'].includes(job.status);

  useEffect(() => {
    if (!job?.id || ['completed', 'failed', 'cancelled'].includes(job.status)) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const state = await pianoRequest<TranscriptionJob>(`/jobs/${job.id}`, { signal: controller.signal });
        if (state.status === 'completed') {
          const result = await pianoRequest<Omit<PianoSong, 'id'>>(`/jobs/${job.id}/result`, { signal: controller.signal });
          imported.current({ ...result, id: job.id });
          setJob(state);
          close.current();
        } else if (['failed', 'cancelled'].includes(state.status)) {
          setJob(state);
          if (state.status === 'failed') setError(state.message);
        } else {
          setJob(state);
          timer = setTimeout(poll, 1500);
        }
      } catch (reason) {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason.message : 'Không đọc được tiến trình.');
        // A temporary lost connection does not abandon an expensive running job.
        timer = setTimeout(poll, 4000);
      }
    };
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [job?.id, job?.status]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setError('');
    const source = youtube.trim() ? 'youtube' : 'file';
    if (source === 'file' && !file) { setError('Bạn chưa chọn file hoặc nhập link YouTube.'); return; }
    if (source === 'youtube' && !youtube.trim()) { setError('Bạn chưa nhập link YouTube.'); return; }
    setSubmitting(true);
    try {
      const data = new FormData();
      if (source === 'file' && file) data.append('file', file);
      else data.append('youtube', youtube.trim());
      setJob(await pianoRequest<TranscriptionJob>('/jobs', { method: 'POST', body: data }));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Không gửi được bản nhạc.');
    } finally { setSubmitting(false); }
  };

  useEffect(() => {
    if (!open) return;
    const onEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') close.current(); };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [open]);

  if (!open) return null;
  const chooseFile = (next: File | null) => {
    setFile(next);
    if (next) { setYoutube(''); setError(''); }
  };
  return (
    <div className={embedded ? 'transcription-entry' : 'piano-import-backdrop'} onClick={event => { if (!embedded && event.target === event.currentTarget) onClose(); }}>
      <div className={embedded ? 'piano-import-shell' : 'transcription-entry transcription-modal'}>
      {!embedded && <button className="piano-import-dismiss" type="button" aria-label="Đóng" onClick={onClose}>×</button>}
      <section className="piano-import" role={embedded ? undefined : 'dialog'} aria-modal={embedded ? undefined : true} aria-labelledby="piano-import-title">
        <span className="piano-import-eyebrow">HARMONY AURALIS · PIANO AI</span>
        <h2 id="piano-import-title">Biến bản nhạc thành piano</h2>
        <p>Chọn một bản thu hoặc video YouTube. AI sẽ chuyển thành MIDI, phổ hai khuông và nốt rơi để bạn nghe và tập theo.</p>
        <form onSubmit={submit}>
            <label className="piano-upload-zone" onDragOver={event => event.preventDefault()} onDrop={event => {
              event.preventDefault();
              if (!busy) chooseFile(event.dataTransfer.files[0] ?? null);
            }}>
              <svg className="upload-cloud" width="48" height="48" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M14 34H10a8 8 0 0 1-1-16 14 14 0 0 1 27-2 9 9 0 0 1 2 18h-5M24 39V20m-7 7 7-7 7 7" /></svg>
              <strong>{file ? file.name : 'Nhập file âm thanh hoặc bản nhạc'}</strong>
              <span className="piano-drop-hint">Hoặc kéo và thả file vào đây</span>
              <span>Âm thanh, video hoặc MIDI · tối đa 100 MB</span>
              <input ref={fileInput} className="piano-file-input" aria-label="Chọn file âm thanh hoặc bản nhạc" type="file" accept=".mp3,.wav,.flac,.m4a,.aac,.ogg,.mp4,.webm,.mid,.midi" disabled={busy} onChange={event => chooseFile(event.target.files?.[0] ?? null)} />
            </label>
          <div className="piano-source-divider"><span>HOẶC</span></div>
            <label className="piano-youtube-label piano-youtube-inline">
              <svg className="piano-youtube-icon" viewBox="0 0 28 20" aria-hidden="true"><rect width="28" height="20" rx="5" fill="currentColor" /><path d="m11 5 8 5-8 5z" fill="#fff" /></svg>
              <input type="url" aria-label="Link YouTube" placeholder="Dán link YouTube tại đây" value={youtube} onChange={event => {
                setYoutube(event.target.value);
                if (event.target.value.trim()) { setFile(null); if (fileInput.current) fileInput.current.value = ''; }
              }} disabled={busy} />
            </label>
          {job && <div className="piano-job-status" role="status"><progress max={100} value={job.progress} /><span>{job.message}</span></div>}
          {error && <p className="piano-import-error" role="alert">{error}</p>}
          <p className="piano-import-note">Tối đa 20 phút mỗi bài. Chuyển nhạc có thể mất vài phút; phổ AI có thể cần chỉnh lại một số nốt.</p>
          <div className="piano-import-actions">
            {busy && job ? <button className="piano-import-cancel" type="button" onClick={async () => {
              try { await pianoRequest(`/jobs/${job.id}/cancel`, { method: 'POST' }); }
              catch (reason) { setError(reason instanceof Error ? reason.message : 'Không hủy được tác vụ.'); }
            }}>Hủy xử lý</button> : null}
            <button type="submit" className="piano-primary" disabled={busy}>{busy ? 'Đang chuyển nhạc…' : 'Chuyển thành piano'}</button>
          </div>
        </form>
      </section>
      </div>
    </div>
  );
}
