---
name: api-music
description: Generate music through a hosted music API with the ElevenLabs music contract (a composition plan of sections with durations and style tags, then audio from a prompt or from that plan), via the bundled scripts/genmusic.py. Use when asked to generate background music, a BGM bed, a score, a jingle or an instrumental through an API rather than a local model, to get a structured, editable composition plan, or to compare an API take with a local (ace-music) take.
---

# Music through an API (ElevenLabs music contract)

**Start here:** read `doc.local.md` in this skill's folder. It is not committed. It gives this
machine's gateway values for the placeholders below: `<base>` (base URL, from an environment
variable), `<prefix>` (the gateway's path prefix for the music API), `<key-env>` (the variable that
holds the API key), `<model>` (the model id the gateway wants), and where outputs went so far.
`scripts/genmusic.py` reads the same values from `config.local.json` next to this file (also not
committed); `doc.local.md` shows its contents. If both are missing, ask the user for the gateway
and write them; never put a URL or key into a committed file.

Compared with `ace-music` (local ACE-Step): no GPU, ~10 s for a 2–3 minute track, structure that
follows a written plan section by section; but every call is billed, there are no seeds, and the
tempo and key are only as exact as the words you give it.

## The three calls

All are `POST`, JSON body, `Authorization: Bearer $<key-env>`, synchronous: the response *is* the
result. No task id, no polling, no cancel.

| Call | Does | Response | Measured time |
|---|---|---|---|
| `<base><prefix>/music/plan` | writes a composition plan only, no audio | JSON `{"chunks": [...]}` | 4–6 s |
| `<base><prefix>/music` | audio | `audio/mpeg` 48 kHz stereo 192 kbps (default); a `song-id` response header | 10 s track: 4.6 s |
| `<base><prefix>/music/detailed` | audio plus the plan it used | `multipart/mixed`: a JSON part, then `music.mp3` | 125 s track: 10 s; 175 s: 12 s |

**The body must carry `"model_id": "<model>"`.** Without it the gateway answers
HTTP 400 `unsupported native endpoint contract for POST …` — the same text as for a wrong path, so
it looks like a routing problem when the path is right. The model id is found in the gateway's
`GET /v1/models` list. (The same error also comes back for `{}`; probe with a minimally valid body.)

### Body fields (confirmed)

- `prompt` + `music_length_ms` — a text description and the length. Without a length the model
  picks one (a short prompt gave 30 s).
- `composition_plan` — instead of `prompt`: a plan from `/music/plan` (or from a `/detailed`
  response), edited. The durations are honoured exactly: two chunks set to 4000 + 6000 ms gave a
  10.03 s file.
- `force_instrumental: true` — no vocals. **Only with `prompt`**: with `composition_plan` it is HTTP 422
  "`force_instrumental` can only be used with `prompt`." — put `vocals` in the chunks'
  `negative_styles` instead (`genmusic.py` drops the flag with a warning).
- Query `?output_format=pcm_48000` — raw 16-bit little-endian stereo PCM (`audio/pcm`, no header;
  10 s = 1,920,000 B). `genmusic.py` asks for it when the output name ends in `.wav` and wraps it;
  it also works with `/music/detailed` (the multipart audio part is then PCM).

### The plan

```json
{"chunks": [
  {"text": "[Intro]", "duration_ms": 30000,
   "positive_styles": ["112 BPM", "D minor", "tight low percussion bed", "..."],
   "negative_styles": ["vocals", "drums"],
   "context_adherence": "high", "conditioning_ref": null, "condition_strength": null}
]}
```

`text` is a section label (for instrumentals); `positive_styles` / `negative_styles` are the
per-section style tags, and this is where tempo, key, instruments and "no drums" belong. The
`/detailed` JSON part also has `song_metadata` (title, genres, …; empty for instrumentals),
`words_timestamps` and `waveform_visual` (both null for instrumentals).

## Use

```bash
S=<this skill's folder>
$S/scripts/genmusic.py plan    --prompt-file cue.txt --length 125 -o cue-plan.json      # cheap, look first
$S/scripts/genmusic.py compose --plan cue-plan.json --detailed -o cue.wav               # audio + cue.json
$S/scripts/genmusic.py compose --prompt-file cue.txt --length 125 --instrumental -o cue.mp3
$S/scripts/genmusic.py compose --plan cue-plan.json -o x.mp3 --dry-run                  # print, no call
```

Python 3, standard library only. `--dry-run` shows the URL with the host masked and the body.

Recommended loop for a bed under narration:

1. `plan` from the prompt and the exact cue length (scene length + a few seconds of tail).
2. Read the chunks. **Write the tempo and key into every chunk's `positive_styles`** and fix the
   section boundaries to the scene's beats (e.g. a hit where the chapter turns). Put `vocals`,
   `drums`, `sudden hits` in `negative_styles` where the voice must stay clear.
3. `compose --plan … --detailed` (no `--instrumental` here; see above); keep the returned plan with the audio, so the take can be
   regenerated or edited section by section.
4. Measure, as for any generated audio (`ace-music/scripts/analyze.py`, `ffmpeg … loudnorm`).

## What came out (2026-11-25, two beds, same prompts as the ACE-Step beds)

Prompt-only requests (no plan editing), `force_instrumental`, 125 s and 175 s:

- **Structure follows the plan it writes**: 4 and 5 named sections, sound continuous to within
  ~2 s of the end. The ACE-Step takes of the same prompts stopped 12 s early or had hard breaks.
- **Tempo and key from the prose were not kept**: asked D major → got A major; asked D minor
  112 BPM → got F minor 128 BPM. With a prompt only, the model invents its own `positive_styles`;
  state them explicitly (step 2 above) or they drift.
- **It can insert silence on its own**: the 175 s take has a ~3 s full stop at ~2:10 ("pre-climax
  break"). Check for gaps before laying a take under narration.
- **Loud**: −13.3 and −12.0 LUFS integrated (ACE-Step takes were −17 to −20). Set the bed gain from
  the measured loudness, not a fixed dB value.

## Cost discipline

Every `compose` bills by length; `plan` produces no audio (2–6 s). Do not sweep parameters with `compose`:
probe a body with `plan` or a 10 s `compose`, then make the one long call. Record what you
generated (length, how many calls) in `doc.local.md`.
