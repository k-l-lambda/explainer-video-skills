"""Rank BGM takes per chapter for use as a bed under narration, and write bgm.json with the best take.

    <audio-python> rank_beds.py [--write]   # copy into <project>/assets/bgm/tools/ first

Expects <project>/assets/bgm/takes/<scene>/ and <project>/assets/narration/timeline.json (scenes with start/end).

For each takes/<S>/<S>-seed<N>.wav, over the scene's length (+3 s tail) from narration/timeline.json:
- short: sound ends before the scene does (hard penalty);
- gaps: seconds where the level falls >30 dB below the take's median (hard breaks);
- hits: broadband transient rate above 4 kHz per second (drum-like hits);
- jumps: count of 1 s windows whose level changes > 9 dB from the previous one (sudden swells or drops);
- centroid: mean spectral centroid (Hz), shown only.
Lower score is better. A listening pass decides in the end; this only sorts.
"""
import argparse, glob, json, os
import numpy as np, librosa

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--write', action='store_true')
ap.add_argument('--gain-db', type=float, default=-22)
a = ap.parse_args()

tl = json.load(open(os.path.join(HERE, '..', 'narration', 'timeline.json')))
pick = {}
for sc in tl['scenes']:
    need = sc['end'] - sc['start'] + 3
    rows = []
    for f in sorted(glob.glob(os.path.join(HERE, 'takes', sc['id'], f"{sc['id']}-seed*.wav"))):
        y, sr = librosa.load(f, sr=22050, mono=True)
        hop = 512
        rms = librosa.feature.rms(y=y, hop_length=hop)[0]
        db = 20 * np.log10(rms + 1e-9)
        loud = np.nonzero(db > db.max() - 45)[0]
        end = (loud[-1] + 1) * hop / sr if len(loud) else 0
        n = int(min(need, len(y) / sr) * sr / hop)
        d = db[:n]
        gaps = float((d < np.median(d) - 30).sum() * hop / sr)
        S = np.abs(librosa.stft(y[: n * hop], n_fft=1024, hop_length=hop))
        hi = S[int(4000 / (sr / 1024)):]
        flux = np.maximum(0, np.diff(hi, axis=1)).sum(0)
        peaks = librosa.util.peak_pick(flux, pre_max=3, post_max=3, pre_avg=10, post_avg=10,
                                       delta=flux.mean() * 2 + 1e-9, wait=5)
        hits = len(peaks) / (n * hop / sr)
        sec = int(sr / hop)
        w = np.array([d[i:i + sec].mean() for i in range(0, len(d) - sec, sec)])
        jumps = int((np.abs(np.diff(w)) > 9).sum())
        cen = float(librosa.feature.spectral_centroid(y=y[: n * hop], sr=sr).mean())
        short = max(0.0, need - end)
        score = short * 5 + gaps * 2 + hits * 10 + jumps * 3
        rows.append((score, os.path.basename(f), end, short, gaps, hits, jumps, cen))
    rows.sort()
    print(f"{sc['id']} (needs {need:.0f} s)")
    for r in rows:
        print(f"  {r[1]:16s} score {r[0]:6.1f}  ends {r[2]:5.1f}  short {r[3]:4.1f}  gaps {r[4]:4.1f}s  "
              f"hits {r[5]:.2f}/s  jumps {r[6]}  centroid {r[7]:.0f}")
    if rows:
        pick[sc['id']] = {'file': f"bgm/takes/{sc['id']}/{rows[0][1]}", 'gain_db': a.gain_db}
if a.write:
    json.dump(pick, open(os.path.join(HERE, 'bgm.json'), 'w'), ensure_ascii=False, indent=1)
    print('wrote bgm.json')
