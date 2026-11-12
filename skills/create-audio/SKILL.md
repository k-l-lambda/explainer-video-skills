---
name: create-audio
description: Generate sound effects with Stable Audio 3 (small-sfx), locally, via the bundled scripts/gen_sfx.py, then rank the takes by prompt match (CLAP) and signal checks with scripts/score.py. Use when asked to make, generate or regenerate sound effects, foley, UI sounds, ambient beds or SFX for an explainer, and to place them against the narration.
---

# Sound effects with Stable Audio 3

**Machine-specific values** go in `doc.local.md` in this skill's folder (ignored by git through `*.local.*`). It gives:

- `<sa3>`: the Stable Audio 3 code and its extra dependencies;
- `<python>`: the interpreter that runs the scripts, with its `PYTHONPATH`;
- where the weights are cached, the proxy for downloads, the GPU, and other GPU users that can be stopped.

If it is missing, ask the user where Stable Audio 3 is installed, and write it.

The scripts are in this skill's `scripts/` folder: `gen_sfx.py` (generate), `score.py` (rank and pick),
`example-sfx.json` (a spec to copy).

## Requirements

- **Code**: https://github.com/Stability-AI/stable-audio-3, MIT licence. `from stable_audio_3 import StableAudioModel`.
- **Weights**: `stabilityai/stable-audio-3-small-sfx` on Hugging Face (about 3.5 GB, with its T5Gemma text
  encoder). It is **gated**: the user has to accept the licence on the model page, logged in, before a download
  with their token works; until then it returns 403. Never look for or borrow someone else's token.
- **Models** (`StableAudioModel.from_pretrained(name)`): `small-sfx` for effects; `small-music` for music;
  `medium` (1.4B, CUDA only) for higher quality; `*-base` variants need `cfg_scale≈7`. Stable Audio 3 Large is
  API only.
- **Hardware**: small-sfx runs on CPU too, but on a CUDA GPU it takes about 0.7 s per take after a 13 s load,
  using about 2 GB of VRAM. A whole set of ~90 takes is a couple of minutes.
- **Scoring**: `transformers` with `laion/larger_clap_general` (about 0.7 GB, downloaded on first use), `librosa`,
  `soundfile`, `torchaudio`.

## Licence of the output

Stability AI Community License (https://stability.ai/license), stated in the model card. Read it on the model
page before publishing; as checked on 2026-11-11:

- commercial use and publication are allowed, and the output belongs to the user;
- commercial use needs registering at stability.ai/community-license; above US$1M annual revenue an enterprise
  licence is needed;
- the T5Gemma text encoder also falls under Gemma's terms of use;
- releasing generated sounds needs no licence text; redistributing the model does.

Ask the user whether their release counts as commercial use. Record the model and the take of every sound you
ship (see "Placing the sounds").

## 1. Write a spec

One entry per sound, in a JSON file (see `scripts/example-sfx.json`):

```json
{"id": "whip-crack", "dur": 1.5, "type": "oneshot", "prompt": "A single sharp leather whip crack, close and dry, cartoon comedy timing, short tail, no music"}
```

- `type`: `oneshot` for one event (a crack, a ding, a click), `texture` for a bed (crowd murmur, keyboard, a machine).
- `dur`: the length you need. For a one-shot it is a maximum; the sound is cut at its end.
- Prompts in English, concrete: the source, the distance ("close", "in a large room"), the character ("dry",
  "glassy"), what to leave out ("no music", "no voices", "no distinct words"). One sound per prompt.
- `"noisy_ok": true` on a one-shot that is noise by nature (a scratch, a sweep, paper), so the scorer does not
  flag its floor.

## 2. Generate candidates

```bash
<python> <skill>/scripts/gen_sfx.py sfx.json candidates --seeds 1,2,3 [--only id,id]
```

- Writes `candidates/<id>/s<seed>.wav` (48 kHz stereo 24-bit) and `candidates/report.json`.
- Each take is cleaned: a 40 Hz high-pass, silence trimmed at 48 dB under the peak, a 5 ms fade-in and a 30 ms
  fade-out, and the peak set to -1 dBFS. **Levels are not set here**; they belong to the mix.
- **Short sounds**: asked for under about 2 s, small-sfx returns steady noise (it scores below zero against its
  prompt). The script generates them at 4 s instead; a one-shot keeps its first event (from the start until the
  level stays 40 dB under the peak for 150 ms), a texture keeps its first `dur` seconds.
- Three to five seeds per sound. Generation is cheap; picking is the work.

## 3. Rank and pick

```bash
<python> <skill>/scripts/score.py sfx.json candidates --pick final
```

- `clap`: cosine between the take and its prompt in LAION CLAP, the main score. Good takes land around 0.3–0.5;
  under 0.25 the sound is usually wrong.
- Checks: `len` against the requested length; `crest` (peak over RMS: high for a crack, low for a bed); `noise`,
  the quietest 10% of 20 ms frames below the peak; `clip`.
- Flags: `short` (a one-shot under 0.15 s, a texture under 60% of `dur`), `clip`, `noisy` (a floor less than 35 dB
  under the peak, one-shots only).
- `--pick` copies the best unflagged take of each sound to `final/<id>.wav`. `candidates/scores.json` keeps every
  score.
- **The score is a first pass, not a verdict.** Someone has to listen, above all to anything with a CLAP under 0.3.

## What it is not for

- **Voices**: a sigh, a "hmm", a confused "uh…" are speech. A diffusion SFX model does not do them well. Use the
  tts skill's VoiceDesign model with a voice description and the exact syllable as the text, and pick by
  transcribing it back and by its pitch contour (for confusion: a rise of a few semitones).
- **Background music**: use a licensed library with clear terms instead, or `small-music` only after checking
  its licence for the release. Many local music models (MusicGen) are non-commercial.

## Placing the sounds

Keep a cue sheet next to the sounds: one entry per use, with the file, the scene, a level in dB, and an **anchor**
instead of a time, so the sound follows the picture when the narration is re-synthesized:

```json
{"scene": "S0", "file": "final/record-scratch.wav", "gain_db": -10, "at": {"cue": "Shall we"},
 "model": "Stable Audio 3 small-sfx, 8 steps, record-scratch/s2.wav (CLAP 0.41)"}
```

Anchors that worked: a sentence's start or end, a word's share of a sentence, a picture cue, a scene edge, each plus
an offset. When a sound must hit an on-screen event whose time lives in the scene's code (a click, a card lighting
up), place it from that code and mark the cue sheet entry as placed by the scene, so there is one source of time.

In Remotion, one `<Sequence from>` with an `<Audio volume>` per sound. Pitfalls met in practice:

- **Keep every source 48 kHz stereo.** A mono file, and `ffmpeg -ac 2`, put the sound about 3 dB lower (a pan
  law). Copy the channel instead: `-af "pan=stereo|c0=c0|c1=c0"`.
- Remotion sums audio with `amix normalize=0`, so levels add up as set.
- **Check placement by subtraction**: render the soundtrack alone (`--codec=wav`), subtract the narration and the
  music stems, and what is left is the effects. Silence where nothing is scheduled proves nothing else leaked in;
  cross-correlating that residual with each file gives its exact onset (within a frame).
- **Loudness last**: master the finished film to about -15 LUFS with one fixed gain and a brick-wall limiter
  (true peak at or under -1 dBTP). Do not use a dynamic loudness normaliser; it raises the beds in every pause.

## Checking a result

- Read the scorer's table: every pick unflagged, CLAP not far below the others for the same sound.
- Look at `report.json` for wall times; at ~0.7 s per take, a much slower run means the GPU is shared.
- Listen. Nothing replaces it, and the scorer cannot tell a funny whip crack from a dull one.
