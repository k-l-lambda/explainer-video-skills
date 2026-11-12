"""Generate sound effects with Stable Audio 3 (small-sfx by default), a few candidates per sound.

    <python> gen_sfx.py SPEC.json OUT_DIR [--seeds 1,2,3] [--only id,id] [--model small-sfx] [--steps 8]

SPEC.json is a list of {id, dur, prompt, type}: `dur` in seconds, `type` "oneshot" (one event: a crack, a ding)
or "texture" (a bed: murmur, keyboard, a machine running).

For each entry {id, dur, prompt} writes OUT_DIR/<id>/s<seed>.wav: stereo 48 kHz, 24-bit, cleaned by clean():
leading and trailing near-silence trimmed, a 40 Hz high-pass for rumble, a 5 ms fade-in and a 30 ms fade-out,
peak at -1 dBFS (levels are set in the mix, from cues.json, not here). OUT_DIR/report.json lists times.
"""
import argparse, json, time
from pathlib import Path
import numpy as np, soundfile as sf, torch, torchaudio
from stable_audio_3 import StableAudioModel

SR = 48000
# Stable Audio 3 small-sfx returns steady noise when asked for under ~2 s. Short sounds are generated at
# MIN_GEN seconds and cut to their first event (first_event), at most the requested length.
MIN_GEN = 4.0

def first_event(x: np.ndarray, sr: int, max_len: float) -> np.ndarray:
    """x: [ch, n] cleaned. Keep from the start to where the level stays 40 dB under the peak for 150 ms."""
    env = np.convolve(np.abs(x).max(0), np.ones(int(0.01 * sr)) / int(0.01 * sr), mode="same")
    low = env < env.max() * 10 ** (-40 / 20); run = int(0.15 * sr); n = x.shape[1]
    end = n
    i = int(0.03 * sr)
    while i < n - run:
        if low[i:i + run].all(): end = i + int(0.05 * sr); break
        i += int(0.01 * sr)
    end = min(end, int(max_len * sr), n)
    y = x[:, :end].copy(); fo = min(end, int(0.03 * sr)); y[:, -fo:] *= np.linspace(1, 0, fo)
    return y

def clean(x: np.ndarray, sr: int) -> np.ndarray:
    """x: [ch, n] float. Trim, high-pass, fade, normalise."""
    x = torchaudio.functional.highpass_biquad(torch.from_numpy(x).float(), sr, 40.0).numpy()
    env = np.abs(x).max(0)
    win = max(1, int(0.01 * sr))
    env = np.convolve(env, np.ones(win) / win, mode="same")
    floor = env.max() * 10 ** (-48 / 20)        # trim to 48 dB below the peak
    on = np.where(env > floor)[0]
    if len(on):
        a = max(0, on[0] - int(0.01 * sr)); b = min(x.shape[1], on[-1] + int(0.05 * sr))
        x = x[:, a:b]
    fi, fo = int(0.005 * sr), int(0.03 * sr)
    if x.shape[1] > fi + fo:
        x[:, :fi] *= np.linspace(0, 1, fi); x[:, -fo:] *= np.linspace(1, 0, fo)
    peak = np.abs(x).max()
    return x * (10 ** (-1 / 20) / peak) if peak > 0 else x

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("out")
    ap.add_argument("--seeds", default="1,2,3"); ap.add_argument("--only"); ap.add_argument("--model", default="small-sfx")
    ap.add_argument("--steps", type=int, default=8)
    a = ap.parse_args()
    spec = json.loads(Path(a.spec).read_text())
    if a.only: spec = [s for s in spec if s["id"] in a.only.split(",")]
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    m = StableAudioModel.from_pretrained(a.model)
    msr = m.model_config["sample_rate"]
    print(f"loaded {a.model} in {time.time() - t0:.1f}s, model sample rate {msr}", flush=True)
    rep = []
    for s in spec:
        d = out / s["id"]; d.mkdir(exist_ok=True)
        for seed in map(int, a.seeds.split(",")):
            t = time.time()
            short = float(s["dur"]) < MIN_GEN
            y = m.generate(prompt=s["prompt"], duration=max(float(s["dur"]), MIN_GEN), steps=a.steps, seed=seed)
            y = y[0].float().cpu()
            if msr != SR: y = torchaudio.functional.resample(y, msr, SR)
            y = clean(y.numpy(), SR)
            if short and s.get("type", "oneshot") == "oneshot": y = first_event(y, SR, float(s["dur"]) * 1.25)
            elif short:   # a texture: keep its first dur seconds, with a fade
                n = min(y.shape[1], int(float(s["dur"]) * SR)); y = y[:, :n].copy(); fo = int(0.15 * SR); y[:, -fo:] *= np.linspace(1, 0, fo)
            sf.write(d / f"s{seed}.wav", y.T, SR, subtype="PCM_24")
            r = dict(id=s["id"], seed=seed, seconds=round(y.shape[1] / SR, 2), wall=round(time.time() - t, 2))
            rep.append(r); print(json.dumps(r), flush=True)
    (out / "report.json").write_text(json.dumps(dict(model=a.model, steps=a.steps, takes=rep), indent=1))

if __name__ == "__main__":
    main()
