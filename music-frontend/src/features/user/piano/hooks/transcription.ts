export type SongNote = { id: string; pitch: number; start: number; end: number; velocity: number; hand: 'L' | 'R' };
export type ScoreEvent = { time: number; on: string[]; off: string[]; page: number | null };
export type PianoSong = {
  editable?: boolean;
  id: string;
  title: string;
  duration: number;
  bpm: number;
  meter: string;
  key: string;
  notes: SongNote[];
  pages: string[];
  timeline: ScoreEvent[];
  originalAudio: string | null;
  downloads: Record<string, string>;
  notice: string;
};
export type TranscriptionJob = { id: string; status: string; progress: number; message: string };

let nativeApiUrl: string | undefined;
export function configurePianoApi(url?: string) { nativeApiUrl = url; }
export function pianoApiUrl() {
  const host = typeof window !== 'undefined' && window.location.hostname;
  const fallback = host && !['localhost', '127.0.0.1', ''].includes(host)
    ? `${window.location.protocol}//${host.includes(':') ? `[${host}]` : host}:8001`
    : 'http://127.0.0.1:8001';
  return (process.env.EXPO_PUBLIC_PIANO_API_URL || nativeApiUrl || fallback).replace(/\/$/, '');
}
export const songAsset = (song: PianoSong, name: string) => `${pianoApiUrl()}/jobs/${song.id}/assets/${encodeURIComponent(name)}`;

export async function pianoRequest<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${pianoApiUrl()}${path}`, options);
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') throw error;
    throw new Error('Không kết nối được dịch vụ chuyển nhạc. Hãy khởi động Piano AI trên backend.');
  }
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Yêu cầu chuyển nhạc thất bại.');
  return body as T;
}

export function midiNoteName(pitch: number) {
  return `${['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][pitch % 12]}${Math.floor(pitch / 12) - 1}`;
}

export function lowerNoteIndex(notes: SongNote[], time: number) {
  let low = 0;
  let high = notes.length;
  while (low < high) {
    const middle = (low + high) >>> 1;
    if (notes[middle].start < time) low = middle + 1;
    else high = middle;
  }
  return low;
}
