from collections import defaultdict
import math
import numpy as np

def estimate_tempo_audio(path, duration, recorded_bpm=None, recorded_reliable=False):
    """Analyze short segments across the COMPLETE file, bounded in memory."""
    try:
        import librosa
    except Exception as exc:
        return None, f"librosa unavailable: {exc}", []
    span = min(45.0, max(12.0, duration * 0.50))
    locations = [0.08, 0.40, 0.72] if duration > 95 else [0.12]
    sr, hop = 11025, 256
    observations = []
    for fraction in locations:
        start = max(0.0, min(duration - span, duration * fraction))
        try:
            y, _ = librosa.load(str(path), sr=sr, mono=True,
                                offset=float(start), duration=float(span))
            if len(y) < sr * 8 or float(np.sqrt(np.mean(y * y))) < 0.0002:
                continue
            onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
            if len(onset) < 30 or float(np.std(onset)) < 0.025:
                continue
            estimated, beat_frames = librosa.beat.beat_track(
                onset_envelope=onset, sr=sr, hop_length=hop,
                start_bpm=85, trim=True,
            )
            bpm = float(np.asarray(estimated).reshape(-1)[0])
            times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
            if len(times) < 5 or not (35 <= bpm <= 250):
                continue
            intervals = np.diff(times)
            if len(intervals) > 3:
                med = float(np.median(intervals))
                regular = 1.0 - min(1.0, float(np.median(np.abs(intervals - med))) / max(0.001, med))
            else:
                regular = 0.0
            observations.append((bpm, regular, round(float(start), 1)))
        except Exception as exc:
            print("Tempo analysis skipped a segment:", str(exc)[:180])
    if not observations:
        return None, "no reliable beat detected", []

    # Fold half/double-tempo observations toward the most consistent tempo.
    # When the original MIDI tempo looks real, it provides a useful anchor.
    ref = recorded_bpm if recorded_reliable else None
    folded = []
    for bpm, quality, start in observations:
        candidates = [c for c in (bpm / 2, bpm, bpm * 2) if 42 <= c <= 210]
        if ref is not None:
            best = min(candidates, key=lambda c: abs(math.log2(c / ref)))
        else:
            # When both plausible, prefer original tracker output unless
            # it is unusually fast: avoid gratuitous half-tempo collapse.
            best = bpm
            if bpm > 145 and bpm / 2 >= 55:
                best = bpm / 2
            elif bpm < 55 and bpm * 2 <= 160:
                best = bpm * 2
        folded.append((best, quality, start))
    final = round(float(np.median([v[0] for v in folded])), 2)
    values = np.asarray([v[0] for v in folded])
    disagreement = float(np.max(values) - np.min(values)) if len(values) > 1 else 0.0
    info = "audio beat tracker (multiple excerpts)" if len(folded) > 1 else "audio beat tracker (one excerpt)"
    if disagreement > max(8.0, final * 0.12):
        info += " - LOW CONFIDENCE: excerpts disagree"
    return final, info, folded

def estimate_meter(midi, bpm):
    signatures = [s for s in midi.time_signature_changes if s.numerator > 0]
    supported = {(2, 4), (3, 4), (4, 4), (6, 8), (9, 8), (12, 8)}
    found = [(int(s.numerator), int(s.denominator)) for s in signatures]
    candidates = [s for s in found if s in supported]
    if candidates and (candidates[0] != (4, 4) or len(candidates) > 1):
        num, den = candidates[0]
        return f"{num}/{den}", "explicit MIDI time signature"
    # Robust, conservative test of triple meter from bass/chord attacks.
    # Without audio/music score reference, avoid confidently hallucinating 6/8.
    events = []
    for inst in midi.instruments:
        if inst.is_drum:
            continue
        for n in inst.notes:
            if n.end <= n.start or n.velocity < 8:
                continue
            index = int(round(n.start * bpm / 60.0))
            error = abs(n.start * bpm / 60.0 - index)
            if error > 0.21:
                continue
            weight = (float(n.velocity) / 127.0) * (1.4 if n.pitch < 53 else 1.0)
            events.append((index, weight))
    if len(events) < 30:
        return "4/4", "conservative fallback (weak meter evidence)"
    acc = defaultdict(float)
    for i, w in events:
        acc[i] += w
    indices = sorted(acc)
    if len(indices) < 20:
        return "4/4", "conservative fallback (too few rhythmic accents)"

    def contrast(period):
        sums = np.zeros(period)
        bins = np.zeros(period)
        for idx in range(indices[0], indices[-1] + 1):
            position = idx % period
            sums[position] += acc[idx]
            bins[position] += 1
        means = sums / np.maximum(1, bins)
        return float((means.max() - means.mean()) / max(0.0001, means.mean()))

    triple, quadruple = contrast(3), contrast(4)
    # Choose 3/4 only when a repeated three-beat accent is distinctly stronger.
    if triple > max(0.42, quadruple * 1.55) and len(indices) >= 36:
        return "3/4", "estimated recurring three-beat accents (uncertain)"
    return "4/4", "automatic conservative default (4/4)"