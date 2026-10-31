# Cell 8 - Self-contained score-engine implementation
"""Self-contained Piano MusicXML engine for a Kaggle transcription notebook.

Input: multi-instrument PrettyMIDI output.
Output: ONE two-staff piano MusicXML, quantized piano MIDI, notes JSON, diagnostics.
Full song duration is preserved; note thinning is optional.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pretty_midi

DIVISIONS = 16  # MusicXML ticks per quarter note


@dataclass
class PianoScoreSettings:
    mode: str = "piano"        # "piano" (readable reduction) or "faithful" (all distinct MIDI pitches)
    bpm: float | None = None   # None: infer from MIDI; overridden value is quarter-note BPM
    time_signature: str = "4/4"
    key_fifths: int | None = None  # None: estimate key signature
    hand_split: int = 60       # MIDI C4
    grid_per_beat: int = 4     # 4: 16th grid; 8: 32nd grid
    right_hand_polyphony: int = 4
    left_hand_polyphony: int = 3
    downbeat_seconds: float = 0.0
    chord_symbols: bool = True  # heuristic from predicted notes, may be wrong
    exclude_track_ids: tuple[int, ...] = ()
    # Full audio duration keeps all pages/blank measures through the audio end.
    full_audio_seconds: float | None = None
    tempo_source: str | None = None
    meter_source: str | None = None


def validate_settings(opts: PianoScoreSettings):
    if opts.mode not in {"piano", "faithful"}:
        raise ValueError("mode must be 'piano' or 'faithful'")
    if opts.grid_per_beat not in (2, 4, 8, 16):
        raise ValueError("grid_per_beat must be 2, 4, 8 or 16")
    if opts.bpm is not None and not (20 <= opts.bpm <= 300):
        raise ValueError("bpm must be 20..300")
    if opts.full_audio_seconds is not None and not (0 < opts.full_audio_seconds < 8*3600):
        raise ValueError("full_audio_seconds must be between 0 and 8 hours")
    if opts.key_fifths is not None and not (-7 <= opts.key_fifths <= 7):
        raise ValueError("key_fifths must be in -7..7")
    if not (24 <= opts.hand_split <= 108):
        raise ValueError("hand_split must be 24..108")
    num, den = parse_time_signature(opts.time_signature)
    if num * DIVISIONS * 4 % den:
        raise ValueError("Time signature cannot be represented with divisions=16")
    return num, den


def parse_time_signature(time_sig):
    parts = time_sig.strip().split("/")
    if len(parts) != 2:
        raise ValueError("Time signature must look like 4/4, 3/4 or 6/8")
    beats, base = int(parts[0]), int(parts[1])
    if not 1 <= beats <= 16 or base not in (2, 4, 8, 16):
        raise ValueError("Unsupported time signature: " + time_sig)
    return beats, base


def choose_bpm(midi, manual_bpm=None):
    if manual_bpm is not None:
        return float(manual_bpm), "manual override"
    try:
        times, tempos = midi.get_tempo_changes()
        vals = np.asarray(tempos, dtype=float)
        good = vals[(vals >= 35) & (vals <= 240)]
        if len(good):
            if len(times) > 1:
                # Pick a duration-weighted tempo instead of assuming the first event.
                boundaries = list(times[1:]) + [max(float(midi.get_end_time()), float(times[-1]))]
                pairs = [(float(t), max(0.0, float(e) - float(s)))
                         for s, e, t in zip(times, boundaries, tempos)
                         if 35 <= float(t) <= 240]
                pairs.sort(key=lambda p: p[0])
                total = sum(d for _, d in pairs)
                acc = 0.0
                if total > 0:
                    for tempo, seconds in pairs:
                        acc += seconds
                        if acc >= total / 2:
                            return round(tempo, 3), "MIDI tempo map (weighted median)"
            return round(float(good[0]), 3), "MIDI tempo"
    except Exception:
        pass
    return 120.0, "fallback (change BPM if incorrect)"


# Krumhansl-Schmuckler key estimation. A transcription may be too noisy to infer it reliably.
_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
_MAJOR_FIFTHS = [0, -5, 2, -3, 4, -1, 6, 1, -4, 3, -2, 5]
_MINOR_FIFTHS = [-3, 4, -1, 6, 1, -4, 3, -2, 5, 0, -5, 2]
_PC_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]


def estimate_key(raw_notes):
    bins = np.zeros(12, dtype=float)
    for n in raw_notes:
        span = min(8.0, max(0.0, n["end_sec"] - n["start_sec"]))
        bins[n["pitch"] % 12] += span * (0.7 + 0.3 * n["velocity"] / 127)
    if not np.any(bins):
        return 0, "C major (fallback)", 0.0
    candidates = []
    for root in range(12):
        for is_minor, template, signatures in [(False, _MAJOR, _MAJOR_FIFTHS), (True, _MINOR, _MINOR_FIFTHS)]:
            profile = np.roll(template, root)
            score = np.corrcoef(bins, profile)[0, 1]
            candidates.append((float(score), signatures[root], f"{_PC_NAMES[root]} {'minor' if is_minor else 'major'}"))
    candidates.sort(reverse=True, key=lambda item: item[0])
    score, fifths, key_name = candidates[0]
    return int(fifths), key_name, round(score, 3)


def read_source_notes(midi, opts):
    rows = []
    ids_to_ignore = set(opts.exclude_track_ids)
    for track_id, instrument in enumerate(midi.instruments):
        if instrument.is_drum or track_id in ids_to_ignore:
            continue
        for index, n in enumerate(instrument.notes):
            if not (0 <= int(n.pitch) <= 127):
                continue
            a, b = float(n.start), float(n.end)
            if not (math.isfinite(a) and math.isfinite(b) and b > a + 0.01):
                continue
            rows.append({"id": f"t{track_id}_n{index}", "source_track": track_id,
                         "pitch": int(n.pitch), "start_sec": max(0.0, a),
                         "end_sec": b, "velocity": int(n.velocity)})
    rows.sort(key=lambda n: (n["start_sec"], n["pitch"], n["end_sec"]))
    return rows


def quantize_notes(raw, bpm, opts):
    tick_step = DIVISIONS // opts.grid_per_beat
    dedup = {}
    for n in raw:
        if n["end_sec"] <= opts.downbeat_seconds:
            continue
        start_seconds = max(0.0, n["start_sec"] - opts.downbeat_seconds)
        end_seconds = max(start_seconds, n["end_sec"] - opts.downbeat_seconds)
        a = max(0, round((start_seconds * bpm / 60 * DIVISIONS) / tick_step) * tick_step)
        b = max(a + tick_step, round((end_seconds * bpm / 60 * DIVISIONS) / tick_step) * tick_step)
        hand = "R" if n["pitch"] >= opts.hand_split else "L"
        key = (hand, int(a), n["pitch"])
        candidate = {"id": n["id"], "source_track": n["source_track"],
                     "hand": hand, "pitch": n["pitch"], "start": int(a),
                     "end": int(b), "velocity": n["velocity"]}
        prev = dedup.get(key)
        if prev is None or (candidate["end"], candidate["velocity"]) > (prev["end"], prev["velocity"]):
            dedup[key] = candidate
    return sorted(dedup.values(), key=lambda n: (n["start"], n["pitch"], n["end"]))


def _priority(n):
    if n["hand"] == "R":
        register = 0.12 * (n["pitch"] - 60)
    else:
        register = 0.12 * (60 - n["pitch"])
    return register + 0.035 * n["velocity"] + 0.01 * min(DIVISIONS * 4, n["end"] - n["start"])


def simplify_piano(notes, opts):
    if opts.mode == "faithful":
        return notes[:], 0
    kept = []
    for hand, cap in (("R", opts.right_hand_polyphony), ("L", opts.left_hand_polyphony)):
        candidates = [n for n in notes if n["hand"] == hand]
        # At equal onset, prioritize melody/top voice (R) and bass (L).
        candidates.sort(key=lambda n: (n["start"], -_priority(n), n["pitch"]))
        active = []
        for n in candidates:
            active = [old for old in active if old["end"] > n["start"]]
            if len(active) < cap:
                kept.append(n)
                active.append(n)
    kept.sort(key=lambda n: (n["start"], n["pitch"], n["end"]))
    return kept, len(notes) - len(kept)


def make_piano_midi(notes, bpm, output_path):
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm, resolution=480)
    for hand, label in (("R", "Piano Right Hand"), ("L", "Piano Left Hand")):
        instrument = pretty_midi.Instrument(program=0, name=label)
        for n in notes:
            if n["hand"] != hand:
                continue
            instrument.notes.append(pretty_midi.Note(
                velocity=int(max(1, min(127, n["velocity"]))),
                pitch=int(n["pitch"]),
                start=max(0.0, float(n["start"]) / DIVISIONS * 60 / bpm),
                end=float(n["end"]) / DIVISIONS * 60 / bpm,
            ))
        pm.instruments.append(instrument)
    pm.write(str(output_path))
    return pm


# MusicXML engraving helpers --------------------------------------------------
_DURATION_TYPES = [
    (128, "breve", 0), (96, "whole", 1), (64, "whole", 0),
    (48, "half", 1), (32, "half", 0),
    (24, "quarter", 1), (16, "quarter", 0),
    (12, "eighth", 1), (8, "eighth", 0),
    (6, "16th", 1), (4, "16th", 0),
    (3, "32nd", 1), (2, "32nd", 0), (1, "64th", 0)
]
_DUR_DICT = {d: (t, dots) for d, t, dots in _DURATION_TYPES}
_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]


def pitch_name(pitch, fifths):
    name = (_FLAT if fifths < 0 else _SHARP)[pitch % 12]
    step = name[0]
    alter = 1 if "#" in name else (-1 if "b" in name else 0)
    octave = pitch // 12 - 1
    return step, alter, octave


def duration_pieces(a, b):
    assert b > a, (a, b)
    out = []
    pos = a
    while pos < b:
        rem = b - pos
        # Avoid a note/rest with an awkward large value starting off the beat.
        allowed = sorted(_DUR_DICT, reverse=True)
        for d in allowed:
            if d > rem:
                continue
            if pos % DIVISIONS != 0 and d >= DIVISIONS and pos + d > ((pos // DIVISIONS) + 1) * DIVISIONS:
                continue
            out.append((pos, d, *_DUR_DICT[d]))
            pos += d
            break
        else:
            raise ValueError(f"Cannot notate duration from {a} to {b} at {pos}")
    return out


def map_notes_to_measures(notes, measure_ticks):
    measures = defaultdict(list)
    for n in notes:
        start_measure = n["start"] // measure_ticks
        end_measure = (n["end"] - 1) // measure_ticks
        for idx in range(start_measure, end_measure + 1):
            s = max(n["start"], idx * measure_ticks)
            e = min(n["end"], (idx + 1) * measure_ticks)
            if e > s:
                measures[idx].append({
                    "pitch": n["pitch"], "hand": n["hand"],
                    "start": s, "end": e,
                    "tie_in": s > n["start"], "tie_out": e < n["end"],
                })
    return measures


def group_to_voices(fragments, hand):
    groups = defaultdict(list)
    for f in fragments:
        if f["hand"] == hand:
            k = (f["start"], f["end"], f["tie_in"], f["tie_out"])
            groups[k].append(int(f["pitch"]))
    units = []
    for (a, b, tie_in, tie_out), pitches in groups.items():
        units.append({"start": a, "end": b, "tie_in": tie_in,
                      "tie_out": tie_out, "pitches": sorted(set(pitches))})
    units.sort(key=lambda u: (u["start"], -(u["end"] - u["start"]), -max(u["pitches"])))
    voices = []
    ends = []
    midpoints = []
    for u in units:
        center = sum(u["pitches"]) / len(u["pitches"])
        valid = [i for i, last_end in enumerate(ends) if last_end <= u["start"]]
        if valid:
            target = min(valid, key=lambda i: abs(midpoints[i] - center))
            voices[target].append(u)
            ends[target] = u["end"]
            midpoints[target] = center
        else:
            voices.append([u])
            ends.append(u["end"])
            midpoints.append(center)
    return voices


def _records_for_voice(groups, begin, end):
    out = []
    cursor = begin
    for group in groups:
        if group["start"] > cursor:
            for s, dur, dtype, dots in duration_pieces(cursor, group["start"]):
                out.append({"is_rest": True, "start": s, "duration": dur,
                            "type": dtype, "dots": dots, "pitches": [],
                            "tie_in": False, "tie_out": False})
        pieces = duration_pieces(group["start"], group["end"])
        for index, (s, dur, dtype, dots) in enumerate(pieces):
            out.append({"is_rest": False, "start": s, "duration": dur,
                        "type": dtype, "dots": dots, "pitches": group["pitches"],
                        "tie_in": group["tie_in"] or index > 0,
                        "tie_out": group["tie_out"] or index < len(pieces) - 1})
        cursor = group["end"]
    if cursor < end:
        for s, dur, dtype, dots in duration_pieces(cursor, end):
            out.append({"is_rest": True, "start": s, "duration": dur,
                        "type": dtype, "dots": dots, "pitches": [],
                        "tie_in": False, "tie_out": False})
    if not out:
        # MusicXML full-measure rest for a completely empty staff.
        out.append({"is_rest": True, "full_measure": True, "start": begin,
                    "duration": end - begin, "type": "whole", "dots": 0,
                    "pitches": [], "tie_in": False, "tie_out": False})
    assert sum(rec["duration"] for rec in out) == end - begin, "Incomplete voice"
    return out


def _beam_count(rec):
    return {"eighth": 1, "16th": 2, "32nd": 3, "64th": 4}.get(rec["type"], 0)


def add_beaming(records, beats, beat_type, bar_start):
    if beats % 3 == 0 and beat_type == 8 and beats > 3:
        beam_group = DIVISIONS * 3 // 2  # e.g. dotted-quarter grouping in 6/8
    else:
        beam_group = DIVISIONS
    run = []

    def flush():
        if len(run) < 2:
            run.clear()
            return
        for index, rec in enumerate(run):
            depth = _beam_count(rec)
            tags = []
            prev = run[index-1] if index > 0 else None
            next_ = run[index+1] if index+1 < len(run) else None
            for level in range(1, depth+1):
                has_prev = prev is not None and _beam_count(prev) >= level
                has_next = next_ is not None and _beam_count(next_) >= level
                if has_prev and has_next: kind = "continue"
                elif has_prev: kind = "end"
                elif has_next: kind = "begin"
                elif level > 1:
                    kind = "backward hook" if prev is not None else "forward hook"
                else:
                    continue
                tags.append((level, kind))
            if tags:
                rec["beams"] = tags
        run.clear()

    for rec in records:
        group_id = (rec["start"] - bar_start) // beam_group
        if rec["is_rest"] or not _beam_count(rec):
            flush()
            continue
        if run:
            prev = run[-1]
            if (prev["start"] + prev["duration"] != rec["start"] or
                    (prev["start"] - bar_start) // beam_group != group_id):
                flush()
        run.append(rec)
    flush()
    return records


def _xml_tag(parent, tag, value=None, **attrib):
    el = ET.SubElement(parent, tag, **{key: str(val) for key, val in attrib.items()})
    if value is not None:
        el.text = str(value)
    return el


def write_note_element(measure, rec, pitch, voice, staff, fifths, is_chord=False):
    n = _xml_tag(measure, "note")
    if is_chord:
        _xml_tag(n, "chord")
    if pitch is None:
        _xml_tag(n, "rest", **({"measure": "yes"} if rec.get("full_measure") else {}))
    else:
        p = _xml_tag(n, "pitch")
        step, alter, octave = pitch_name(pitch, fifths)
        _xml_tag(p, "step", step)
        if alter:
            _xml_tag(p, "alter", alter)
        _xml_tag(p, "octave", octave)
    _xml_tag(n, "duration", rec["duration"])
    if pitch is not None:
        if rec["tie_in"]:
            _xml_tag(n, "tie", type="stop")
        if rec["tie_out"]:
            _xml_tag(n, "tie", type="start")
    _xml_tag(n, "voice", voice)
    _xml_tag(n, "type", rec["type"])
    for _ in range(rec["dots"]):
        _xml_tag(n, "dot")
    _xml_tag(n, "staff", staff)
    if not is_chord:
        for level, kind in rec.get("beams", []):
            _xml_tag(n, "beam", kind, number=level)
    if pitch is not None and (rec["tie_in"] or rec["tie_out"]):
        nts = _xml_tag(n, "notations")
        if rec["tie_in"]:
            _xml_tag(nts, "tied", type="stop")
        if rec["tie_out"]:
            _xml_tag(nts, "tied", type="start")
    return n


# Chord Symbols: infer harmony from the notes in overlapping beat windows.
# These are estimates from the MIDI transcription, not verified chord labels.
# Each tuple: MusicXML chord kind, pitch-class intervals, visible suffix.
_CHORDS = [
    ("dominant",            (0, 4, 7, 10), "7"),
    ("major-seventh",       (0, 4, 7, 11), "maj7"),
    ("minor-seventh",       (0, 3, 7, 10), "m7"),
    ("half-diminished",     (0, 3, 6, 10), "m7b5"),
    ("diminished-seventh",  (0, 3, 6, 9),  "dim7"),
    ("major-sixth",         (0, 4, 7, 9),  "6"),
    ("minor-sixth",         (0, 3, 7, 9),  "m6"),
    ("major",               (0, 4, 7),     ""),
    ("minor",               (0, 3, 7),     "m"),
    ("diminished",          (0, 3, 6),     "dim"),
    ("augmented",           (0, 4, 8),     "aug"),
    ("suspended-fourth",    (0, 5, 7),     "sus4"),
    ("suspended-second",    (0, 2, 7),     "sus2"),
]
_CHORD_SUFFIX = {kind: suffix for kind, _, suffix in _CHORDS}


def find_chord(notes, start_tick, end_tick):
    """Estimate a chord for a short musical window using weighted note overlap.

    Unlike reading only the notes on beat 1, this also handles arpeggiated
    chords and changes of harmony in the second half of a measure.
    Returns (root_pc, musicxml_kind, bass_pc, confidence) or None.
    """
    span = max(1, end_tick - start_tick)
    weights = [0.0] * 12
    overlapped = []
    for n in notes:
        overlap = max(0, min(end_tick, n["end"]) - max(start_tick, n["start"]))
        if overlap <= 0:
            continue
        pitch = int(n["pitch"])
        velocity = float(n.get("velocity", 85))
        weight = overlap / span * (0.75 + min(127, velocity) / 508.0)
        if pitch < 60:
            weight *= 1.30  # bass is often a stronger harmonic cue
        elif pitch >= 81 and (n["end"] - n["start"]) <= DIVISIONS:
            weight *= 0.65  # avoid over-weighting short lead/melody notes
        weights[pitch % 12] += weight
        overlapped.append((n, overlap))
    total = sum(weights)
    if not overlapped or total < 0.6:
        return None
    max_weight = max(weights)
    meaningful = max(0.10, max_weight * 0.11)
    if sum(v >= meaningful for v in weights) < 3:
        return None

    # Choose a bass sustained through the beginning or a large part of window.
    bass_candidates = [
        (float(overlap), -int(n["pitch"]), n)
        for n, overlap in overlapped
        if int(n["pitch"]) <= 64 and overlap >= max(2, span * 0.20)
    ]
    bass_pc = None
    if bass_candidates:
        low = min(int(candidate[2]["pitch"]) for candidate in bass_candidates)
        nearby = [c for c in bass_candidates if c[2]["pitch"] <= low + 7]
        bass = max(nearby, key=lambda c: (c[0], c[1]))[2]
        bass_pc = int(bass["pitch"]) % 12

    winners = []
    for root in range(12):
        for kind, intervals, _ in _CHORDS:
            required = [(root + x) % 12 for x in intervals]
            support = [weights[p] for p in required]
            if min(support) < meaningful:
                continue
            included = sum(support)
            coverage = included / total
            if coverage < (0.66 if len(intervals) >= 4 else 0.69):
                continue
            # Prefer complete seventh chords when seventh is a stable note.
            score = coverage * 100.0 + 1.3 * len(intervals)
            score += 2.8 if bass_pc == root else 0.0
            if bass_pc is not None and bass_pc in required:
                score += 0.6
            winners.append((score, root, kind, coverage, tuple(required)))
    if not winners:
        return None
    winners.sort(key=lambda w: w[0], reverse=True)
    best = winners[0]
    # If two different chord roots have effectively the same evidence, omit.
    if len(winners) > 1 and abs(winners[1][0] - best[0]) < 0.65 and winners[1][1] != best[1]:
        return None
    _, root, kind, coverage, chord_pcs = best
    # Only print /bass when it is reasonably a chord-tone inversion.
    use_bass = bass_pc if bass_pc in chord_pcs else root
    return int(root), str(kind), int(use_bass), round(float(coverage), 3)


def detect_chord_events(notes, measure_ticks, beats, beat_type, measure_count):
    """Place chord symbols at the starts of 1- or 2-beat harmonic windows."""
    if beat_type == 8 and beats in (6, 9, 12):
        interval = 3 * DIVISIONS // 2  # dotted quarter in compound meter
    else:
        interval = 2 * DIVISIONS if beats >= 4 else DIVISIONS
    events = defaultdict(list)
    prev = None
    all_events = []
    for bar_index in range(measure_count):
        start = bar_index * measure_ticks
        end = start + measure_ticks
        for pos in range(start, end, interval):
            chord = find_chord(notes, pos, min(end, pos + interval))
            if chord is None:
                continue
            identity = chord[:3]
            # Periodically repeat unchanged chord for readers of a long score.
            if identity == prev and not (bar_index % 4 == 0 and pos == start):
                continue
            events[bar_index].append((pos - start, chord))
            root, kind, bass, confidence = chord
            all_events.append({
                "measure": bar_index + 1,
                "offset_ticks": pos - start,
                "start_beat": round(pos / DIVISIONS, 3),
                "root_pitch_class": root,
                "kind": kind,
                "bass_pitch_class": bass,
                "confidence_heuristic": confidence,
            })
            prev = identity
    return events, all_events


def _chord_symbol(measure, chord, fifths, offset_ticks=0):
    root_pc, quality, bass_pc, _ = chord
    obj = _xml_tag(measure, "harmony", placement="above", **{"font-size": "11"})
    root = _xml_tag(obj, "root")
    step, alter, _ = pitch_name(root_pc + 60, fifths)
    _xml_tag(root, "root-step", step)
    if alter:
        _xml_tag(root, "root-alter", alter)
    suffix = _CHORD_SUFFIX[quality]
    attrs = {"text": suffix} if suffix else {}
    _xml_tag(obj, "kind", quality, **attrs)
    if bass_pc != root_pc:
        bass = _xml_tag(obj, "bass")
        step_b, alter_b, _ = pitch_name(bass_pc + 60, fifths)
        _xml_tag(bass, "bass-step", step_b)
        if alter_b:
            _xml_tag(bass, "bass-alter", alter_b)
    if offset_ticks:
        _xml_tag(obj, "offset", int(offset_ticks))
    _xml_tag(obj, "staff", 1)
    return obj


def build_musicxml(notes, opts, bpm, fifths, title, xml_path):
    beats, beat_type = validate_settings(opts)
    measure_ticks = beats * 4 * DIVISIONS // beat_type
    last_tick = max((n["end"] for n in notes), default=0)
    if opts.full_audio_seconds is not None:
        # Include ALL audio: a completely untranscribed tail becomes rests,
        # not silently a truncated score. This is not a claim that AI heard it.
        audio_end_tick = math.ceil(
            max(0.0, opts.full_audio_seconds - opts.downbeat_seconds)
            * bpm / 60.0 * DIVISIONS
        )
        last_tick = max(last_tick, audio_end_tick)
    measure_count = (last_tick + measure_ticks - 1) // measure_ticks
    spans = map_notes_to_measures(notes, measure_ticks)
    score = ET.Element("score-partwise", version="4.0")
    work = _xml_tag(score, "work")
    _xml_tag(work, "work-title", title)
    _xml_tag(score, "movement-title", title)
    identity = _xml_tag(score, "identification")
    _xml_tag(identity, "creator", "AI transcription - editable draft", type="composer")
    defaults = _xml_tag(score, "defaults")
    scale = _xml_tag(defaults, "scaling")
    _xml_tag(scale, "millimeters", 7)
    _xml_tag(scale, "tenths", 40)
    # A4 landscape page layout, in MusicXML tenths, for downstream editors.
    page_layout = _xml_tag(defaults, "page-layout")
    _xml_tag(page_layout, "page-height", 1200)
    _xml_tag(page_layout, "page-width", 1697)
    margins = _xml_tag(page_layout, "page-margins", type="both")
    _xml_tag(margins, "left-margin", 55)
    _xml_tag(margins, "right-margin", 55)
    _xml_tag(margins, "top-margin", 50)
    _xml_tag(margins, "bottom-margin", 50)
    system_layout = _xml_tag(defaults, "system-layout")
    system_margins = _xml_tag(system_layout, "system-margins")
    _xml_tag(system_margins, "left-margin", 0)
    _xml_tag(system_margins, "right-margin", 0)
    _xml_tag(system_layout, "system-distance", 145)
    part_list = _xml_tag(score, "part-list")
    part_info = _xml_tag(part_list, "score-part", id="P1")
    _xml_tag(part_info, "part-name", "Piano")
    _xml_tag(part_info, "part-abbreviation", "Pno.")
    instr = _xml_tag(part_info, "score-instrument", id="Ipiano")
    _xml_tag(instr, "instrument-name", "Piano")
    gm = _xml_tag(part_info, "midi-instrument", id="Ipiano")
    _xml_tag(gm, "midi-channel", 1)
    _xml_tag(gm, "midi-program", 1)  # MusicXML counts programs from 1
    part = _xml_tag(score, "part", id="P1")
    if opts.chord_symbols:
        chord_by_bar, chord_events = detect_chord_events(
            notes, measure_ticks, beats, beat_type, measure_count)
    else:
        chord_by_bar, chord_events = {}, []
    total_written_notes = 0
    max_voices = 0
    for i in range(measure_count):
        start = i * measure_ticks
        end = start + measure_ticks
        bar = _xml_tag(part, "measure", number=i+1, implicit="no")
        if i == 0:
            attrs = _xml_tag(bar, "attributes")
            _xml_tag(attrs, "divisions", DIVISIONS)
            key = _xml_tag(attrs, "key")
            _xml_tag(key, "fifths", fifths)
            time = _xml_tag(attrs, "time")
            _xml_tag(time, "beats", beats)
            _xml_tag(time, "beat-type", beat_type)
            _xml_tag(attrs, "staves", 2)
            clef1 = _xml_tag(attrs, "clef", number=1)
            _xml_tag(clef1, "sign", "G")
            _xml_tag(clef1, "line", 2)
            clef2 = _xml_tag(attrs, "clef", number=2)
            _xml_tag(clef2, "sign", "F")
            _xml_tag(clef2, "line", 4)
            direction = _xml_tag(bar, "direction", placement="above")
            dirtype = _xml_tag(direction, "direction-type")
            metronome = _xml_tag(dirtype, "metronome", parentheses="no")
            _xml_tag(metronome, "beat-unit", "quarter")
            _xml_tag(metronome, "per-minute", f"{bpm:g}")
            _xml_tag(direction, "staff", 1)
            _xml_tag(direction, "sound", tempo=f"{bpm:g}")
        fragments = spans.get(i, [])
        for offset_ticks, chord in chord_by_bar.get(i, []):
            _chord_symbol(bar, chord, fifths, offset_ticks=offset_ticks)
        all_voices = []
        for hand, staff, initial_voice in (("R", 1, 1), ("L", 2, 11)):
            voices = group_to_voices(fragments, hand)
            if not voices:
                voices = [[]]
            max_voices = max(max_voices, len(voices))
            for j, groups in enumerate(voices):
                records = _records_for_voice(groups, start, end)
                add_beaming(records, beats, beat_type, start)
                all_voices.append((initial_voice + j, staff, records))
        for vi, (voice_no, staff, records) in enumerate(all_voices):
            if vi:
                backup = _xml_tag(bar, "backup")
                _xml_tag(backup, "duration", measure_ticks)
            for rec in records:
                pitches = rec["pitches"] if not rec["is_rest"] else [None]
                for j, pitch in enumerate(pitches):
                    write_note_element(bar, rec, pitch, voice_no, staff, fifths, is_chord=j>0)
                    if pitch is not None:
                        total_written_notes += 1
        if i == measure_count - 1:
            final = _xml_tag(bar, "barline", location="right")
            _xml_tag(final, "bar-style", "light-heavy")
    if hasattr(ET, "indent"):
        ET.indent(score, space="  ")
    ET.ElementTree(score).write(str(xml_path), encoding="utf-8", xml_declaration=True)
    return {"bars": measure_count, "meter": opts.time_signature,
            "written_note_heads_including_ties": total_written_notes,
            "max_voices_per_staff": max_voices, "measures_with_notes": len(spans),
            "chord_symbols_written": len(chord_events),
            "measures_with_chords": len(chord_by_bar),
            "_chord_events": chord_events}


def create_piano_score(midi_path, out_dir, opts: PianoScoreSettings, title="Piano - Full Song"):
    validate_settings(opts)
    midi_path = Path(midi_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    original = pretty_midi.PrettyMIDI(str(midi_path))
    raw = read_source_notes(original, opts)
    if not raw:
        raise ValueError("There are no pitched (non-drum) MIDI notes to create a piano score.")
    bpm, tempo_source = choose_bpm(original, opts.bpm)
    if opts.key_fifths is None:
        fifths, key_name, key_conf = estimate_key(raw)
        key_source = f"estimated {key_name} (correlation {key_conf})"
    else:
        fifths, key_source = opts.key_fifths, "manual override"
    quantized = quantize_notes(raw, bpm, opts)
    notes, removed = simplify_piano(quantized, opts)
    if not notes:
        raise ValueError("All detected notes were removed by the piano arrangement filter.")
    xml_path = out_dir / "piano.musicxml"
    midi_out = out_dir / "piano.mid"
    json_path = out_dir / "piano_notes.json"
    make_piano_midi(notes, bpm, midi_out)
    score_stats = build_musicxml(notes, opts, bpm, fifths, title, xml_path)
    chord_events = score_stats.pop("_chord_events")
    chords_path = out_dir / "piano_chords.json"
    chords_path.write_text(json.dumps(chord_events, ensure_ascii=False, indent=2), encoding="utf-8")
    json_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {
        "midi_input": str(midi_path),
        "piano_midi": str(midi_out),
        "musicxml": str(xml_path),
        "notes_json": str(json_path),
        "chords_json": str(chords_path),
        "raw_note_events": len(raw),
        "quantized_unique_notes": len(quantized),
        "piano_notes": len(notes),
        "notes_removed_for_playability": removed,
        "bpm": bpm, "tempo_source": opts.tempo_source or tempo_source,
        "meter_source": opts.meter_source or "supplied time signature",
        "source_audio_duration_seconds": opts.full_audio_seconds,
        "key_fifths": fifths, "key_source": key_source,
        "mode": opts.mode,
        "chord_symbols": opts.chord_symbols,
        **score_stats,
    }
    (out_dir / "score_diagnostics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
