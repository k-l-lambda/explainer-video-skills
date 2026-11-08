# `scripts/` — verify-loop toolkit

Deterministic helpers the agent **calls** instead of hand-rolling, to close every skill's
*deliver-and-verify* loop: freeze a moment, see start/mid/end at a glance, and assert the
encoded file's real spec. Small, dependency-light, tier-matched.

| Script | Tier | What it does |
|---|---|---|
| `seek-shot.sh` | **Light** (standalone HTML) | Drives the page's `?t=N` seek harness and screenshots each frozen moment. |
| `contact-sheet.sh` | any | Tiles the frames side-by-side into one image (start \| mid \| end) for one-glance review. |
| `probe-mp4.sh` | **Heavy** (Remotion / Manim) | Reads + asserts the MP4's real resolution / codec / fps / duration. |
| `video-sheet.sh` | any video | Timestamped contact sheet straight from a video segment (or the whole film, evenly spaced). |
| `shot-stats.py` | any video | Cuts, ASL, bursts (whip/flash false positives), longest takes, per chapter. |
| `sub-pacing.py` | `.vtt` / `.srt` | Speech rate (CJK chars/s, words/min), coverage, pauses, question lines, chapter open/close lines. |
| `audio-stats.sh` | any video/audio | Integrated LUFS, LRA, true peak, silences. |

## Usage by tier

**Light — standalone HTML** (`?t=N` harness): freeze, shoot, tile.
```bash
scripts/seek-shot.sh anim.html 0 1.5 3        # → frame-0.png frame-1.5.png frame-3.png
scripts/contact-sheet.sh sheet.png frame-*.png
# inspect sheet.png: matches the brief? clipped text / off-canvas / FOUC?
```

**Heavy — Remotion**: render stills with the *real* shipped props, tile, then assert the MP4.
```bash
npx remotion still Short out/f-hook.png --frame=10 --props='{...}'
npx remotion still Short out/f-mid.png  --frame=N  --props='{...}'
npx remotion still Short out/f-end.png  --frame=L  --props='{...}'
scripts/contact-sheet.sh sheet.png out/f-hook.png out/f-mid.png out/f-end.png
npx remotion render Short out/short.mp4 --props='{...}'
scripts/probe-mp4.sh out/short.mp4 1080x1920 30      # vertical short contract
```

**Heavy — Manim**: save the last frame (`-s`) / a range (`-n a,b`), tile, assert.
```bash
manim -s -ql scene.py MyScene                        # media/images/.../MyScene.png
scripts/probe-mp4.sh media/videos/scene/480p15/MyScene.mp4
```

**Analyze — a reference film, or your own long render** (see `reference-video-analysis`, `longform-explainer`):
```bash
scripts/video-sheet.sh film.mp4 overview.jpg 0 auto 6x5 300      # whole film at a glance
python scripts/shot-stats.py film.mp4 --chapters film.info.json  # cut rhythm per chapter
python scripts/sub-pacing.py film.vtt --chapters film.info.json  # script rhythm per chapter
scripts/audio-stats.sh film.mp4                                  # LUFS / LRA / silences
scripts/video-sheet.sh film.mp4 burst.jpg 33.8 0.4               # look where the numbers point
```
Chapters come from yt-dlp's `.info.json` or a TSV of `mm:ss<TAB>title` lines.

## Requirements
- `seek-shot.sh` → `npx` + Playwright Chromium (`npx playwright install chromium` once).
- `contact-sheet.sh` / `probe-mp4.sh` / `video-sheet.sh` / `audio-stats.sh` → `ffmpeg` / `ffprobe` (`video-sheet.sh` stamps timecodes if ffmpeg has `drawtext`).
- `shot-stats.py` / `sub-pacing.py` → Python 3.8+, standard library only (`shot-stats.py` also calls `ffmpeg`).

Shell scripts are POSIX `bash`; run everything from the project where your deliverable lives.
