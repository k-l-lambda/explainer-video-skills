"""Rank the sound-effect candidates, since nobody listened yet: prompt match plus basic signal checks.

    <python> score.py SPEC.json CANDIDATES_DIR [--pick FINAL_DIR]

Per take:
- clap: cosine between the take and its prompt in LAION CLAP (laion/larger_clap_general), the main score;
- len: seconds after trimming, against the requested length;
- crest: peak / RMS in dB (a crack or a ding is high, a bed is low);
- noise: the quietest 10% of 20 ms frames, in dB below the peak (a lower number means a noisier floor);
- clip: share of samples at or above -0.1 dBFS.
A take is flagged when it is under 40% of the requested length, has a floor less than 35 dB under its peak (for
one-shots), or clips. Textures, and entries with "noisy_ok": true (a scratch, a pencil, a sweep), are
not flagged for their floor: a continuous sound has no silence to measure. With --pick, the best unflagged take of each sound is copied to that folder as <id>.wav.
Writes candidates/scores.json.
"""
import argparse, json, shutil
from pathlib import Path
import numpy as np, soundfile as sf, torch, librosa
from transformers import ClapModel, ClapProcessor


def emb(out):
    """CLAP's get_*_features returns a tensor in older transformers and a model output in newer ones."""
    if isinstance(out, torch.Tensor): return out
    for k in ("text_embeds", "audio_embeds", "pooler_output"):
        v = getattr(out, k, None)
        if v is not None: return v
    raise TypeError(f"unexpected CLAP output {type(out).__name__}")

def audio_inputs(pr, y, sr):
    """The processor's keyword is `audios` in transformers 4.x and `audio` in 5.x."""
    try:
        return pr(audio=[y], sampling_rate=sr, return_tensors="pt")
    except (TypeError, ValueError):
        return pr(audios=[y], sampling_rate=sr, return_tensors="pt")

def quiet_ok(s):
    """A continuous sound has no quiet frames, so its 'floor' is not noise."""
    return s.get("type") == "texture" or bool(s.get("noisy_ok"))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("cand"); ap.add_argument("--pick")
    a = ap.parse_args()
    spec = {s["id"]: s for s in json.loads(Path(a.spec).read_text())}
    cand = Path(a.cand)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    m = ClapModel.from_pretrained("laion/larger_clap_general").to(dev).eval()
    pr = ClapProcessor.from_pretrained("laion/larger_clap_general")
    rows = []
    for sid, s in spec.items():
        d = cand / sid
        files = sorted(d.glob("s*.wav")) if d.exists() else []
        if not files: continue
        with torch.no_grad():
            te = emb(m.get_text_features(**pr(text=[s["prompt"]], return_tensors="pt", padding=True).to(dev)))
            te = te / te.norm(dim=-1, keepdim=True)
        for f in files:
            x, sr = sf.read(f, dtype="float32", always_2d=True); mono = x.mean(1)
            y48 = librosa.resample(mono, orig_sr=sr, target_sr=48000)
            with torch.no_grad():
                ae = emb(m.get_audio_features(**audio_inputs(pr, y48, 48000).to(dev)))
                ae = ae / ae.norm(dim=-1, keepdim=True)
            clap = float((ae @ te.T).item())
            peak = np.abs(mono).max() + 1e-9; rms = np.sqrt((mono ** 2).mean()) + 1e-9
            fr = librosa.util.frame(mono, frame_length=960, hop_length=960) if len(mono) >= 960 else mono[None]
            fr_rms = np.sqrt((fr ** 2).mean(0)) + 1e-9
            floor = 20 * np.log10(np.percentile(fr_rms, 10) / peak)
            # Plain floats: newer numpy keeps float32 through round(), which json cannot write.
            r = dict(id=sid, file=str(f.relative_to(cand)), clap=round(float(clap), 3), len=round(len(mono) / sr, 2), want=s["dur"],
                     crest=round(float(20 * np.log10(peak / rms)), 1), noise=round(float(floor), 1),
                     clip=round(float((np.abs(x) >= 10 ** (-0.1 / 20)).mean()), 4))
            r["flags"] = [k for k, bad in [("short", r["len"] < (0.15 if s.get("type") == "oneshot" else 0.6 * s["dur"])), ("clip", r["clip"] > 0.001),
                                           ("noisy", not quiet_ok(s) and r["noise"] > -35)] if bad]
            rows.append(r)
    (cand / "scores.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    best = {}
    for r in rows:
        k = (bool(r["flags"]), -r["clap"])
        if r["id"] not in best or k < best[r["id"]][0]: best[r["id"]] = (k, r)
    for sid, (_, r) in best.items():
        others = sorted(x["clap"] for x in rows if x["id"] == sid)
        print(f"{sid:18s} pick {r['file']:24s} clap {r['clap']:.3f} (all {others})  len {r['len']}/{r['want']}  crest {r['crest']}  floor {r['noise']}  {r['flags'] or ''}")
        if a.pick:
            Path(a.pick).mkdir(parents=True, exist_ok=True); shutil.copy(cand / r["file"], Path(a.pick) / f"{sid}.wav")

if __name__ == "__main__":
    main()
