'use dom';

import React, { useCallback, useMemo, useState, useEffect, useRef } from 'react';
import { useWindowDimensions } from 'react-native';
import Icon from './PianoControlIcon';
import { usePianoAudio } from '../hooks/usePianoAudio';
import './piano.css';
import PianoStaff from './PianoStaff';
import PianoImport from './PianoImport';
import PianoSongPlayer from './PianoSongPlayer';
import { configurePianoApi, type PianoSong } from '../hooks/transcription';
import './transcription.css';
import './mobile.css';
import { pianoPublicAsset } from '../hooks/public-assets';

const allNotes: string[] = [];
allNotes.push("A0", "A#0", "B0");
[1, 2, 3, 4, 5, 6, 7].forEach(octave => {
  "CDEFGAB".split('').forEach(letter => {
    allNotes.push(`${letter}${octave}`);
    if (letter !== 'E' && letter !== 'B') {
      allNotes.push(`${letter}#${octave}`);
    }
  });
});
allNotes.push('C8');

const noteToLabel = (note: string) => {
  if (note.includes('#')) {
    const A = note[0];
    const octave = note[2];
    const aSharp = A + '♯';
    const B = A === 'G' ? 'A' : String.fromCharCode(A.charCodeAt(0) + 1);
    const bFlat = B + '♭';
    return (
      <>
        <span>{aSharp}<sub>{octave}</sub></span>
        <br />
        <span>{bFlat}<sub>{octave}</sub></span>
      </>
    );
  } else {
    const letter = note[0];
    const octave = note[1];
    return <>{letter}<sub>{octave}</sub></>;
  }
};

const KEYBOARD_MAP: Record<string, string> = {
  'KeyA': 'C4', 'KeyW': 'C#4', 'KeyS': 'D4', 'KeyE': 'D#4', 'KeyD': 'E4',
  'KeyF': 'F4', 'KeyT': 'F#4', 'KeyG': 'G4', 'KeyY': 'G#4', 'KeyH': 'A4',
  'KeyU': 'A#4', 'KeyJ': 'B4', 'KeyK': 'C5', 'KeyO': 'C#5', 'KeyL': 'D5',
  'KeyP': 'D#5', 'Semicolon': 'E5', 'Quote': 'F5',
};

const PianoKey = React.memo(function PianoKey({ note, hue, pressed, velocity, onPlay, onStop }: {
  note: string;
  hue: number;
  pressed: boolean;
  velocity: number;
  onPlay: (note: string) => void;
  onStop: (note: string) => void;
}) {
  return (
    <button
      data-note={note}
      className={pressed ? 'pressed' : ''}
      style={{ '--key-hue': hue, '--velocity': velocity } as React.CSSProperties}
      onPointerDown={event => {
        if (event.pointerType === 'touch') return;
        event.preventDefault();
        if (event.button === 0) onPlay(note);
      }}
      onPointerEnter={event => { if (event.pointerType !== 'touch' && event.buttons === 1) onPlay(note); }}
      onPointerLeave={event => { if (event.pointerType !== 'touch' && event.buttons === 1) onStop(note); }}
      onPointerUp={event => { if (event.pointerType !== 'touch' && event.button === 0) onStop(note); }}
      onPointerCancel={event => { if (event.pointerType !== 'touch') onStop(note); }}
      aria-label={`Nốt ${note}`}
      tabIndex={-1}
    >
      <span>{noteToLabel(note)}</span>
    </button>
  );
});

export default function PianoKeyboard({ apiUrl, nativeHost = false, initialSong = null, startInEdition = false, workspace = false, onNewTranscription, onProjectUpdate, onEditionChange }: {
  apiUrl?: string;
  nativeHost?: boolean;
  initialSong?: PianoSong | null;
  startInEdition?: boolean;
  workspace?: boolean;
  onNewTranscription?: () => void;
  onProjectUpdate?: (song: PianoSong, previousId?: string) => void;
  onEditionChange?: (edition: boolean) => void;
  dom?: import('expo/dom').DOMProps;
}) {
  const { width, height } = useWindowDimensions();
  const compact = width < 900;
  const [rangeStart, setRangeStart] = useState(39); // C4
  const [showAllKeys, setShowAllKeys] = useState(false);
  const rangeCount = width > height ? 25 : 13;
  useEffect(() => { configurePianoApi(apiUrl); }, [apiUrl]);
  const pianoAudio = usePianoAudio();
  const { isReady, pressNote, releaseNote, setGlobalVolume } = pianoAudio;
  const [importOpen, setImportOpen] = useState(false);
  const [song, setSong] = useState<PianoSong | null>(initialSong);
  const [playbackKeys, setPlaybackKeys] = useState<Set<string>>(new Set());
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set());
  const pressedKeysRef = useRef<Set<string>>(new Set());

  const [volume, setVolume] = useState(80);
  const [muted, setMuted] = useState(false);
  const [showVelocity, setShowVelocity] = useState(false);
  const [noteVelocities, setNoteVelocities] = useState<Record<string, number>>({});
  const [showEffects, setShowEffects] = useState(false);
  const [staffState, setStaffState] = useState(1); // 0: hidden, 1: treble, 2: both
  const [labelStateIndex, setLabelStateIndex] = useState(1); // 0: '', 1: 'letters', 2: 'letters numbers'

  type RollNote = { id: number, state: 'pressed' | 'released' };
  const [rollHistory, setRollHistory] = useState<Record<string, RollNote[]>>({});
  const rollIdRef = useRef(0);

  const getButtonStateClass = (val: number | boolean) => {
    if (typeof val === 'boolean') return val ? 'on' : '';
    if (val === 1) return 'on';
    if (val === 2) return 'onon';
    if (val === 3) return 'ononon';
    return '';
  };

  useEffect(() => {
    if (setGlobalVolume) {
      setGlobalVolume(muted ? 0 : volume / 100);
    }
  }, [volume, muted, setGlobalVolume]);

  const keysByTouchesRef = useRef<Record<number, string>>({});

  const playNote = useCallback((note: string) => {
    if (pressedKeysRef.current.has(note)) return;
    // Start audio before scheduling visual updates.
    void pressNote(note, volume / 100);
    pressedKeysRef.current.add(note);
    setPressedKeys(new Set(pressedKeysRef.current));
    setNoteVelocities(prev => ({ ...prev, [note]: volume / 100 }));

    if (showEffects) {
      const id = ++rollIdRef.current;
      setRollHistory(prev => ({
        ...prev,
        [note]: [...(prev[note] || []), { id, state: 'pressed' }],
      }));
    }
  }, [pressNote, volume, showEffects]);

  const stopNote = useCallback((note: string) => {
    if (!pressedKeysRef.current.has(note)) return;
    releaseNote(note);
    pressedKeysRef.current.delete(note);
    setPressedKeys(new Set(pressedKeysRef.current));

    if (showEffects) {
      setRollHistory(prev => {
        const notes = prev[note];
        if (!notes?.length || notes[notes.length - 1].state !== 'pressed') return prev;
        return {
          ...prev,
          [note]: notes.map((roll, index) => index === notes.length - 1
            ? { ...roll, state: 'released' }
            : roll),
        };
      });
    }
  }, [releaseNote, showEffects]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
      const target = event.target;
      if (target instanceof HTMLElement && (target.isContentEditable || target.closest('input, textarea, select, button'))) return;
      const note = KEYBOARD_MAP[event.code];
      if (note) {
        event.preventDefault();
        playNote(note);
      }
    };
    const handleKeyUp = (event: KeyboardEvent) => {
      const note = KEYBOARD_MAP[event.code];
      if (note) stopNote(note);
    };
    const releasePressedNotes = () => {
      for (const note of pressedKeysRef.current) stopNote(note);
      keysByTouchesRef.current = {};
    };
    const handleVisibilityChange = () => { if (document.hidden) releasePressedNotes(); };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('blur', releasePressedNotes);
    window.addEventListener('pagehide', releasePressedNotes);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('blur', releasePressedNotes);
      window.removeEventListener('pagehide', releasePressedNotes);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [playNote, stopNote]);
  // Touch Handlers
  const getNoteFromTouch = (touch: React.Touch) => {
    const el = document.elementFromPoint(touch.clientX, touch.clientY);
    if (!el) return null;
    const key = el.closest('button[data-note]');
    return key ? key.getAttribute('data-note') : null;
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    // e.preventDefault(); // Might cause issues with passive listener, use css touch-action instead
    Array.from(e.changedTouches).forEach(touch => {
      const note = getNoteFromTouch(touch);
      if (note) {
        playNote(note);
        keysByTouchesRef.current[touch.identifier] = note;
      }
    });
  };

  const releaseTouch = (id: number) => {
    const note = keysByTouchesRef.current[id];
    delete keysByTouchesRef.current[id];
    if (note && !Object.values(keysByTouchesRef.current).includes(note)) stopNote(note);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    Array.from(e.targetTouches).forEach(touch => {
      const note = getNoteFromTouch(touch);
      const id = touch.identifier;
      const currentNote = keysByTouchesRef.current[id];

      if (note && note !== currentNote) {
        if (currentNote) releaseTouch(id);
        playNote(note);
        keysByTouchesRef.current[id] = note;
      } else if (!note && currentNote) {
        releaseTouch(id);
      }
    });
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    Array.from(e.changedTouches).forEach(touch => {
      const id = touch.identifier;
      releaseTouch(id);
    });
  };

  const keysData = useMemo(() => {
    const keys = allNotes.map((note, i) => {
      const hue = 360 * ((i - 3) / 12);
      const isBlack = note.includes('#');
      return { note, hue, isBlack };
    });
    if (!compact || showAllKeys || song) return keys;
    const start = Math.min(rangeStart, allNotes.length - rangeCount);
    return keys.slice(start, start + rangeCount);
  }, [compact, showAllKeys, song, rangeStart, rangeCount]);

  // Mảng nốt nhạc cho khuông nhạc (Staff notes)
  return (
    <div
      className={`piano-page ${workspace ? 'studio-piano' : ''} ${showEffects ? 'effects-enabled' : ''} ${song ? 'has-song' : ''} ${nativeHost ? 'native-host' : ''} ${compact && !showAllKeys && !song ? 'zoomed-keys' : ''}`}
      style={{
        '--piano-smoke': `url("${pianoPublicAsset('img/smoke_blur.webp')}")`,
        '--piano-smoke-layer': `url("${pianoPublicAsset('img/smoke_layer1_blur.webp')}")`,
      } as React.CSSProperties}
    >
      {nativeHost && <style>{`@font-face { font-family: Bravura; src: url(${JSON.stringify(pianoPublicAsset('font/Bravura.woff2'))}); }`}</style>}
      <PianoImport
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={value => {
          pianoAudio.allOff();
          setPlaybackKeys(new Set());
          setSong({ ...value, notes: [...value.notes].sort((a, b) => a.start - b.start) });
        }}
      />
      <div className="background" aria-hidden="true">
        {Array.from({ length: compact ? 2 : workspace ? 3 : 8 }, (_, index) => (
          <div key={index} className="smoke" />
        ))}
      </div>

      <div className="content">
        <div className="chat-sidebar"></div>
        <div className="main-content">
          <div className="info-row">
            {song ? <PianoSongPlayer
              song={song}
              audio={pianoAudio}
              startInEdition={startInEdition}
              onEditionChange={onEditionChange}
              onNewTranscription={onNewTranscription || (() => setImportOpen(true))}
              onSongChange={updated => { onProjectUpdate?.(updated, song.id); setSong(updated); }}
              onActiveNotes={setPlaybackKeys}
              onClose={() => { setSong(null); setPlaybackKeys(new Set()); }}
            /> : <div className="staff-paper" hidden={staffState === 0}>
              <PianoStaff pressedKeys={pressedKeys} showBass={staffState === 2} />
              <div className="chord-info">
                <b id="chord-name">
                  {!isReady ? 'Loading audio...' : ''}
                </b>
              </div>
            </div>}
          </div>

          {compact && !song && <div className="piano-range-controls" aria-label="Quãng bàn phím">
            <button disabled={showAllKeys || rangeStart === 0} onClick={() => setRangeStart(value => Math.max(0, value - 12))} aria-label="Quãng thấp hơn">‹</button>
            <span>{keysData[0].note} – {keysData[keysData.length - 1].note}</span>
            <button disabled={showAllKeys || rangeStart >= allNotes.length - rangeCount} onClick={() => setRangeStart(value => Math.min(allNotes.length - rangeCount, value + 12))} aria-label="Quãng cao hơn">›</button>
            <button aria-pressed={showAllKeys} onClick={() => setShowAllKeys(value => !value)}>{showAllKeys ? 'Phóng phím' : '88 phím'}</button>
          </div>}
          <div
            className={`keyboard ${['', 'letters', 'letters numbers'][labelStateIndex]} ${showVelocity ? 'velocity' : ''}`}
            style={{ touchAction: 'none' }}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd}
          >
            {showEffects && <div className="pianoroll">
              {keysData.map(k => (
                <div key={k.note} data-note={k.note} style={{ '--key-hue': k.hue } as any}>
                  {(rollHistory[k.note] || []).map(roll => (
                    <React.Fragment key={roll.id}>
                      <div className={`back ${roll.state}`}></div>
                      <div
                        className={`front ${roll.state}`}
                        onAnimationEnd={event => {
                          if (event.animationName !== 'rise-up') return;
                          setRollHistory(prev => ({
                            ...prev,
                            [k.note]: (prev[k.note] || []).filter(item => item.id !== roll.id),
                          }));
                        }}
                      ></div>
                    </React.Fragment>
                  ))}
                </div>
              ))}
            </div>}
            <div className="top-keys">
              {keysData.map(k => (
                <PianoKey
                  key={k.note}
                  note={k.note}
                  hue={k.hue}
                  pressed={pressedKeys.has(k.note) || playbackKeys.has(k.note)}
                  velocity={noteVelocities[k.note] ?? 0}
                  onPlay={playNote}
                  onStop={stopNote}
                />
              ))}
            </div>
            <div className="bottom-keys">
              {keysData.filter(k => !k.isBlack).map(k => (
                <PianoKey
                  key={k.note}
                  note={k.note}
                  hue={k.hue}
                  pressed={pressedKeys.has(k.note) || playbackKeys.has(k.note)}
                  velocity={noteVelocities[k.note] ?? 0}
                  onPlay={playNote}
                  onStop={stopNote}
                />
              ))}
            </div>
          </div>

          <div className="bar tool-bar">
            <div id="instrument-app" className="tool-bar">
              <div>
                <button id="instrument-label" title="Chọn file hoặc link YouTube" aria-label="Nhập bản nhạc để chuyển thành piano" onClick={() => setImportOpen(true)}>
                  <span>
                    <Icon icon="mdi-piano" />
                  </span>
                </button>
                <label className="volume-label" title="volume" tabIndex={0}>
                  <span className="volume-icon" id="mute-span" onClick={() => setMuted(!muted)}>
                    {muted ? (
                      <Icon icon="mdi-volume-mute" />
                    ) : volume > 65 ? (
                      <Icon icon="mdi-volume-high" />
                    ) : volume > 30 ? (
                      <Icon icon="mdi-volume-medium" />
                    ) : (
                      <Icon icon="mdi-volume-low" />
                    )}
                  </span>
                  <input
                    id="volume"
                    type="range"
                    className="volume"
                    min="0" max="100" step="1"
                    value={volume}
                    onChange={(e) => setVolume(Number(e.target.value))}
                    disabled={muted}
                    tabIndex={-1}
                  />
                </label>
              </div>
            </div>

            <div>
              <div>
                <button id="toggle-score" title="show staff" aria-label="toggle show staff" onClick={() => setStaffState(prev => (prev + 1) % 3)} className={getButtonStateClass(staffState)}>
                  <Icon icon="mdi-music-clef-treble" />
                </button>
                <button id="toggle-qwerty" hidden title="show keyboard mapping" aria-label="toggle show keyboard mapping">
                  <Icon icon="mdi-keyboard-outline" />
                </button>
                <button id="toggle-labels" title="show note labels" aria-label="toggle show note labels" onClick={() => setLabelStateIndex(prev => (prev + 1) % 3)} className={getButtonStateClass(labelStateIndex)}>
                  <Icon icon="mdi-label-outline" />
                </button>
                <button
                  id="toggle-velocity"
                  title="show velocity"
                  aria-label="toggle show velocity"
                  aria-pressed={showVelocity}
                  onClick={() => setShowVelocity(current => !current)}
                  className={getButtonStateClass(showVelocity)}
                >
                  <Icon icon="mdi-glass-stange" />
                </button>
              </div>
              <div>
                <button
                  id="toggle-cinema"
                  title="Cinema effects"
                  aria-label="toggle cinema effects"
                  aria-pressed={showEffects}
                  onClick={() => {
                    setRollHistory({});
                    setShowEffects(current => !current);
                  }}
                  className={getButtonStateClass(showEffects)}
                >
                  <Icon icon="mdi-television-clean" />
                </button>
              </div>
            </div>

            <div id="recorder-app">
              <div>
                <button>
                  <Icon icon="mdi-record" />
                </button>
                <button>
                  <Icon icon="mdi-play" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
