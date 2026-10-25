import { useCallback, useEffect, useRef, useState } from 'react';
import type { Context, Sampler } from 'tone';

export const usePianoAudio = () => {
  const samplerRef = useRef<Sampler | null>(null);
  const ToneRef = useRef<typeof import('tone') | null>(null);
  const activeNotesRef = useRef(new Map<string, symbol>());
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let mounted = true;
    const activeNotes = activeNotesRef.current;
    let context: Context | undefined;
    (async () => {
      try {
        // Load Tone.js dynamically only on the client (browser) to avoid Server-Side Rendering (SSR) issues
        const Tone = await import('tone');
        if (!mounted) return;
        ToneRef.current = Tone;

        context = new Tone.Context({
          latencyHint: 'interactive',
          lookAhead: 0,
        });
        Tone.setContext(context);

        const sampler = new Tone.Sampler({
          urls: {
            "A0" : "A0.mp3", "C1" : "C1.mp3", "D#1" : "Ds1.mp3", "F#1" : "Fs1.mp3",
            "A1" : "A1.mp3", "C2" : "C2.mp3", "D#2" : "Ds2.mp3", "F#2" : "Fs2.mp3",
            "A2" : "A2.mp3", "C3" : "C3.mp3", "D#3" : "Ds3.mp3", "F#3" : "Fs3.mp3",
            "A3" : "A3.mp3", "C4" : "C4.mp3", "D#4" : "Ds4.mp3", "F#4" : "Fs4.mp3",
            "A4" : "A4.mp3", "C5" : "C5.mp3", "D#5" : "Ds5.mp3", "F#5" : "Fs5.mp3",
            "A5" : "A5.mp3", "C6" : "C6.mp3", "D#6" : "Ds6.mp3", "F#6" : "Fs6.mp3",
            "A6" : "A6.mp3", "C7" : "C7.mp3", "D#7" : "Ds7.mp3", "F#7" : "Fs7.mp3",
            "A7" : "A7.mp3", "C8" : "C8.mp3"
          },
          baseUrl: "/audio/salamander/",
          release: 1,
          onload: () => {
            if (mounted) setIsReady(true);
          },
        }).toDestination();

        samplerRef.current = sampler;
      } catch (e) {
        console.error("Failed to load Tone.js", e);
      }
    })();

    return () => {
      mounted = false;
      activeNotes.clear();
      if (samplerRef.current) {
        samplerRef.current.dispose();
        samplerRef.current = null;
      }
      void context?.close();
    };
  }, []);

  const pressNote = useCallback(async (note: string, velocity: number = 0.5) => {
    if (!ToneRef.current || !samplerRef.current?.loaded) return;
    const Tone = ToneRef.current;
    const pressId = Symbol(note);
    activeNotesRef.current.set(note, pressId);
    if (Tone.context.state !== 'running') {
      await Tone.start();
    }
    if (samplerRef.current?.loaded && activeNotesRef.current.get(note) === pressId) {
      samplerRef.current.triggerAttack(note, Tone.getContext().immediate(), velocity);
    }
  }, []);

  const releaseNote = useCallback((note: string) => {
    activeNotesRef.current.delete(note);
    if (samplerRef.current?.loaded && ToneRef.current) {
      samplerRef.current.triggerRelease(note, ToneRef.current.getContext().immediate());
    }
  }, []);

  const allOff = useCallback(() => {
    activeNotesRef.current.clear();
    if (samplerRef.current?.loaded) {
      samplerRef.current.releaseAll();
    }
  }, []);

  const setGlobalVolume = useCallback((vol: number) => {
    if (ToneRef.current && ToneRef.current.getDestination) {
      // Convert linear volume (0-1) to Decibels
      const db = vol <= 0 ? -Infinity : 20 * Math.log10(vol);
      ToneRef.current.getDestination().volume.value = db;
    }
  }, []);

  return {
    isReady,
    pressNote,
    releaseNote,
    allOff,
    setGlobalVolume
  };
};
