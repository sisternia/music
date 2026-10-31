import { useState } from 'react';
import type { useScoreEditor } from './useScoreEditor';

export const paletteDurations = [
  { value: 0.25, type: 'long', label: 'Longa' },
  { value: 0.5, type: 'breve', label: 'Nốt tròn kép' },
  { value: 1, type: 'whole', label: 'Nốt tròn' },
  { value: 2, type: 'half', label: 'Nốt trắng' },
  { value: 4, type: 'quarter', label: 'Nốt đen' },
  { value: 8, type: 'eighth', label: 'Nốt móc đơn' },
  { value: 16, type: '16th', label: 'Nốt móc kép' },
  { value: 32, type: '32nd', label: 'Nốt móc ba' },
  { value: 64, type: '64th', label: 'Nốt móc bốn' },
  { value: 128, type: '128th', label: 'Nốt móc năm' },
  { value: 256, type: '256th', label: 'Nốt móc sáu' },
  { value: 512, type: '512th', label: 'Nốt móc bảy' },
];
export const voiceColors = ['#3279bf', '#2c8e78', '#ae792c', '#8650a3', '#3279bf', '#ab578a', '#7c8b31', '#b28032'];

type Input = { duration: number; rest: boolean; dotted: boolean; voice: number; accidental: string; grace: string; slur: boolean; tie: boolean; articulations: string[] };

export function usePaletteSelection(editor: ReturnType<typeof useScoreEditor>) {
  const [input, setInput] = useState<Input>({ duration: 4, rest: false, dotted: false, voice: 1, accidental: '', grace: '', slur: false, tie: false, articulations: [] });
  const active = editor.notes.filter(note => editor.selected.includes(note.id));
  const all = (predicate: (note: typeof active[number]) => boolean) => active.length > 0 && active.every(predicate);
  const duration = active.length ? paletteDurations.find(option => all(note => note.duration === option.type))?.value : input.duration;
  const rest = active.length ? all(note => note.rest) : input.rest;
  const dotted = active.length ? all(note => note.dots > 0) : input.dotted;
  const voice = active.length ? Number(active.find(note => all(item => item.voice === note.voice))?.voice || input.voice) : input.voice;
  const accidental = active.length ? active.find(note => all(item => item.accidental === note.accidental))?.accidental || '' : input.accidental;
  const grace = active.find(note => note.grace)?.grace || input.grace;
  const articulations = active.length ? ['accent', 'strong-accent', 'staccato', 'tenuto'].filter(value => all(note => !!note.articulations?.includes(value))) : input.articulations;
  const slur = active.length ? active.some(note => note.slur) : input.slur;
  const tie = active.length ? active.some(note => note.tie) : input.tie;

  const action = (name: string, value?: string | number) => {
    if (editor.busy) return;
    setInput(current => {
      const next = { ...current, duration: duration ?? current.duration, rest, dotted, voice, accidental, grace, articulations, slur, tie };
      if (name === 'duration') next.duration = Number(value);
      if (name === 'rest') next.rest = !rest;
      if (name === 'dot') next.dotted = !dotted;
      if (name === 'voice') next.voice = Number(value);
      if (name === 'accidental') next.accidental = String(value);
      if (name === 'grace') next.grace = grace === value ? '' : String(value);
      if (name === 'slur') next.slur = !slur;
      if (name === 'tie') next.tie = !tie;
      if (name === 'articulation') next.articulations = articulations.includes(String(value)) ? articulations.filter(item => item !== value) : [...articulations, String(value)];
      return next;
    });
    // With no score selection the palette is a preview of the chosen combination.
    if (active.length) void editor.apply(name, name === 'rest' && rest ? 'note' : value);
  };
  return { active, duration, rest, dotted, voice, accidental, grace, articulations, slur, tie, action, color: voiceColors[voice - 1] || voiceColors[0] };
}
