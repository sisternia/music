import React, { useMemo, useState, useEffect, useRef } from 'react';
import { Icon } from '@iconify/react';
import { usePianoAudio } from '../hooks/usePianoAudio';
import './piano.css';

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

export const PianoKeyboard = () => {
  const { isReady, pressNote, releaseNote, setGlobalVolume } = usePianoAudio();
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set());
  const pressedKeysRef = useRef<Set<string>>(new Set());

  const [volume, setVolume] = useState(80);
  const [muted, setMuted] = useState(false);
  const [octaveShift, setOctaveShift] = useState(0); // in rems or index
  const [isCinema, setIsCinema] = useState(false);
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

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.repeat) return;
    const note = KEYBOARD_MAP[e.code];
    if (note && !pressedKeysRef.current.has(note)) {
      pressedKeysRef.current.add(note);
      setPressedKeys(new Set(pressedKeysRef.current));
      pressNote(note, volume / 100);

      const id = ++rollIdRef.current;
      setRollHistory(prev => ({
        ...prev,
        [note]: [...(prev[note] || []), { id, state: 'pressed' }]
      }));
    }
  };

  const handleKeyUp = (e: KeyboardEvent) => {
    const note = KEYBOARD_MAP[e.code];
    if (note && pressedKeysRef.current.has(note)) {
      pressedKeysRef.current.delete(note);
      setPressedKeys(new Set(pressedKeysRef.current));
      releaseNote(note);

      setRollHistory(prev => {
        const notes = prev[note] || [];
        const last = notes[notes.length - 1];
        if (last && last.state === 'pressed') {
          const updated = [...notes];
          updated[updated.length - 1] = { ...last, state: 'released' };

          // Cleanup after 5s (duration of rise-up animation)
          setTimeout(() => {
            setRollHistory(curr => ({
              ...curr,
              [note]: curr[note]?.filter(n => n.id !== last.id) || []
            }));
          }, 5000);

          return { ...prev, [note]: updated };
        }
        return prev;
      });
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;



    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [pressNote, releaseNote, volume]);

  const keysByTouchesRef = useRef<Record<number, string>>({});

  const playNote = (note: string) => {
    if (!pressedKeysRef.current.has(note)) {
      pressedKeysRef.current.add(note);
      setPressedKeys(new Set(pressedKeysRef.current));
      pressNote(note, volume / 100);

      const id = ++rollIdRef.current;
      setRollHistory(prev => ({
        ...prev,
        [note]: [...(prev[note] || []), { id, state: 'pressed' }]
      }));
    }
  };

  const stopNote = (note: string) => {
    if (pressedKeysRef.current.has(note)) {
      pressedKeysRef.current.delete(note);
      setPressedKeys(new Set(pressedKeysRef.current));
      releaseNote(note);

      setRollHistory(prev => {
        const notes = prev[note] || [];
        const last = notes[notes.length - 1];
        if (last && last.state === 'pressed') {
          const updated = [...notes];
          updated[updated.length - 1] = { ...last, state: 'released' };

          setTimeout(() => {
            setRollHistory(curr => ({
              ...curr,
              [note]: curr[note]?.filter(n => n.id !== last.id) || []
            }));
          }, 5000);

          return { ...prev, [note]: updated };
        }
        return prev;
      });
    }
  };

  // Mouse Handlers
  const handleMouseDown = (e: React.MouseEvent, note: string) => {
    e.preventDefault();
    if (e.button === 0) playNote(note);
  };
  const handleMouseEnter = (e: React.MouseEvent, note: string) => {
    if (e.buttons === 1) playNote(note);
  };
  const handleMouseLeave = (e: React.MouseEvent, note: string) => {
    if (e.buttons === 1) stopNote(note);
  };
  const handleMouseUp = (e: React.MouseEvent, note: string) => {
    if (e.button === 0) stopNote(note);
  };

  // Touch Handlers
  const getNoteFromTouch = (touch: React.Touch) => {
    const el = document.elementFromPoint(touch.clientX, touch.clientY);
    if (!el) return null;
    const key = el.closest('button[data-note]');
    return key ? key.getAttribute('data-note') : null;
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    // e.preventDefault(); // Might cause issues with passive listener, use css touch-action instead
    Array.from(e.targetTouches).forEach(touch => {
      const note = getNoteFromTouch(touch);
      if (note) {
        playNote(note);
        keysByTouchesRef.current[touch.identifier] = note;
      }
    });
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    Array.from(e.targetTouches).forEach(touch => {
      const note = getNoteFromTouch(touch);
      const id = touch.identifier;
      const currentNote = keysByTouchesRef.current[id];

      if (note && note !== currentNote) {
        if (currentNote) stopNote(currentNote);
        playNote(note);
        keysByTouchesRef.current[id] = note;
      } else if (!note && currentNote) {
        stopNote(currentNote);
        delete keysByTouchesRef.current[id];
      }
    });
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    Array.from(e.changedTouches).forEach(touch => {
      const id = touch.identifier;
      const note = keysByTouchesRef.current[id];
      if (note) {
        stopNote(note);
        delete keysByTouchesRef.current[id];
      }
    });
  };

  const keysData = useMemo(() => {
    return allNotes.map((note, i) => {
      const hue = 360 * ((i - 3) / 12);
      const isBlack = note.includes('#');
      return { note, hue, isBlack };
    });
  }, []);

  const shiftLeft = () => setOctaveShift(prev => Math.min(prev + 21, 63));
  const shiftRight = () => setOctaveShift(prev => Math.max(prev - 21, -63));
  const shiftMid = () => setOctaveShift(0);

  // default initial shift for C4 to be near middle
  useEffect(() => {
    shiftMid();
  }, []);

  // Mảng nốt nhạc cho khuông nhạc (Staff notes)
  const TREBLE_NOTES = [
    'C4', 'D4', 'E4', 'F4', 'G4', 'A4', 'B4',
    'C5', 'D5', 'E5', 'F5', 'G5', 'A5', 'B5',
    'C6',
  ];
  const BASS_NOTES = [
    'C2', 'D2', 'E2', 'F2', 'G2', 'A2', 'B2',
    'C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3',
    'C4',
  ];

  const renderStaffNotes = (notesList: string[], isTreble: boolean) => {
    const voffset = isTreble ? -0.125 : 0.125;
    const hspace = 0.25;
    const hoffset = 3.6;
    const vspace = 0.125;

    const els = [];
    notesList.forEach((ch, i) => {
      els.push(
        <span
          key={ch}
          data-note={ch}
          className={pressedKeys.has(ch) ? 'pressed' : ''}
          style={{
            top: `${(-i + 3) * vspace + voffset}em`,
            right: `${i * -hspace + hoffset}em`
          }}
        >
          𝅗
        </span>
      );
      if ((isTreble && ch === 'C6') || (!isTreble && ch === 'C4')) return;

      const sharpCh = ch.replace(/([A-G])(\d)/, '$1#$2');
      els.push(
        <span
          key={sharpCh}
          data-note={sharpCh}
          className={pressedKeys.has(sharpCh) ? 'pressed' : ''}
          style={{
            top: `${(-i + 3) * vspace + voffset}em`,
            right: `${i * -hspace + hoffset}em`
          }}
        >
          {'♯\u2009𝅗'}
        </span>
      );
    });
    return els;
  };

  return (
    <div className={`piano-page ${isCinema ? 'cinema' : ''}`}>
      <div className="cinema-bar" style={{ zIndex: 1000 }}>
        <button id="fullscreen" title="toggle fullscreen" data-placement="bottom" onClick={() => {
          if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => { });
          } else {
            if (document.exitFullscreen) {
              document.exitFullscreen();
            }
          }
        }}>
          <Icon icon="mdi-fullscreen" />
        </button>
        <button id="cinema-off" title="close cinema mode" data-placement="bottom" onClick={() => setIsCinema(false)}>
          <Icon icon="mdi-close" />
        </button>
      </div>

      <div className="back-background"></div>
      <div className="background">
        {[...Array(8)].map((_, i) => <div key={i} className="smoke"></div>)}
      </div>

      <header className="bar">
        <div>
          <a id="home-link" href="#">
            <h1 id="logo">Pianco</h1>
          </a>
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
            <button id="toggle-velocity" title="show velocity" aria-label="toggle show velocity">
              <Icon icon="mdi-glass-stange" />
            </button>
          </div>
          <div>
            <button id="toggle-cinema" title="cinema mode" aria-label="enter cinema mode" onClick={() => setIsCinema(true)}>
              <Icon icon="mdi-television-clean" />
            </button>
          </div>
        </div>
      </header>

      <div className="content">
        <div className="chat-sidebar"></div>
        <div className="main-content">
          <div className="info-row">
            <div className="staff-paper" hidden={staffState === 0}>
              <div className="staffs">
                <div className="staff treble" hidden={staffState < 1}>
                  <span><i>𝄞</i>𝄚𝄚𝄚𝄚𝄚𝄚𝄚𝄚𝄚</span>
                  {renderStaffNotes(TREBLE_NOTES, true)}
                </div>
                <div className="staff bass" hidden={staffState < 2}>
                  <span><i>𝄢</i>𝄚𝄚𝄚𝄚𝄚𝄚𝄚𝄚𝄚</span>
                  {renderStaffNotes(BASS_NOTES, false)}
                </div>
              </div>
              <div className="chord-info">
                <b id="chord-name">
                  {!isReady ? 'Loading audio...' : ''}
                </b>
              </div>
            </div>
          </div>

          <div
            className={`keyboard ${['', 'letters', 'letters numbers'][labelStateIndex]}`}
            style={{ left: `${octaveShift}rem`, touchAction: 'none' }}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
            onTouchCancel={handleTouchEnd}
          >
            <div className="pianoroll">
              {keysData.map(k => (
                <div key={k.note} data-note={k.note} style={{ '--key-hue': k.hue } as any}>
                  {(rollHistory[k.note] || []).map(roll => (
                    <React.Fragment key={roll.id}>
                      <div className={`back ${roll.state}`}></div>
                      <div className={`front ${roll.state}`}></div>
                    </React.Fragment>
                  ))}
                </div>
              ))}
            </div>
            <div className="top-keys">
              {keysData.map(k => (
                <button
                  key={k.note}
                  data-note={k.note}
                  className={pressedKeys.has(k.note) ? 'pressed' : ''}
                  style={{ '--key-hue': k.hue } as any}
                  onMouseDown={(e) => handleMouseDown(e, k.note)}
                  onMouseEnter={(e) => handleMouseEnter(e, k.note)}
                  onMouseLeave={(e) => handleMouseLeave(e, k.note)}
                  onMouseUp={(e) => handleMouseUp(e, k.note)}
                  tabIndex={-1}
                >
                  <span>{noteToLabel(k.note)}</span>
                </button>
              ))}
            </div>
            <div className="bottom-keys">
              {keysData.filter(k => !k.isBlack).map(k => (
                <button
                  key={k.note}
                  data-note={k.note}
                  className={pressedKeys.has(k.note) ? 'pressed' : ''}
                  style={{ '--key-hue': k.hue } as any}
                  onMouseDown={(e) => handleMouseDown(e, k.note)}
                  onMouseEnter={(e) => handleMouseEnter(e, k.note)}
                  onMouseLeave={(e) => handleMouseLeave(e, k.note)}
                  onMouseUp={(e) => handleMouseUp(e, k.note)}
                  tabIndex={-1}
                >
                  <span>{noteToLabel(k.note)}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="bar tool-bar">
            <div id="instrument-app" className="tool-bar">
              <div>
                <label id="instrument-label" htmlFor="instrument">
                  <span>
                    <Icon icon="mdi-piano" />
                  </span>
                </label>
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

            <div id="arrows-app">
              <button id="go-down" title="shift left" aria-label="shift octave down" onClick={shiftLeft}>
                <Icon icon="mdi-chevron-left" />
              </button>
              <button id="go-mid" title="shift to middle" aria-label="return to mid octave" onClick={shiftMid}>
                <Icon icon="mdi-chevron-up" />
              </button>
              <button id="go-up" title="shift right" aria-label="shift octave up" onClick={shiftRight}>
                <Icon icon="mdi-chevron-right" />
              </button>
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
};
