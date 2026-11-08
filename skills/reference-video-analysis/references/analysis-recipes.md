# Analysis Recipes — Cookbook

Commands, thresholds and templates for measuring a reference film and checking what the numbers point at.

## 1. Acquire (analysis copy only)

```bash
mkdir -p ref/VIDEO_ID && cd ref/VIDEO_ID
yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 \
       --write-info-json --write-subs --write-auto-subs --sub-langs "en.*,zh.*" --sub-format vtt \
       -o "%(id)s.%(ext)s" "https://youtu.be/VIDEO_ID"
```

- `.info.json` carries `chapters`, `duration`, `fps`, description (often a source list).
- Prefer manual subtitles over auto-generated; auto subs roll and duplicate lines (`sub-pacing.py` merges consecutive duplicates).
- Keep the copy in a scratch/analysis folder. Don't commit it or derived frames to a deliverable repo.
- AV1 downloads decode fine with ffmpeg ≥ 5 (`libdav1d`); re-encode only if a tool can't read them.

Chapters as TSV (when there's no `.info.json`, or for your own film):

```
# start<TAB>title
00:00	Cold open
01:42	The case
04:21	Foundations
```

## 2. Cut rhythm — `scripts/shot-stats.py`

```bash
python scripts/shot-stats.py film.mp4 --chapters film.info.json --json shots.json
python scripts/shot-stats.py film.mp4 --threshold 0.25      # more sensitive (collage/typography films)
```

- Scene score threshold 0.3 is a good default for edited footage; 0.2–0.25 catches more collage swaps (and more noise); 0.4 only hard cuts.
- Detection runs on a 480px downscale and is cached per threshold (`film.mp4.cuts-0.30.txt`). A 35-min 1080p AV1 film takes ~4 min.
- **Bursts**: raw cuts closer than `--burst` (0.5s) are merged into one event, and runs of ≥ 3 are listed. Report merged ASL as the edit rhythm, and inspect every burst.
- **Longest takes**: may be a hold *or* a continuous camera move. A sheet tells you which.
- Shots that straddle a chapter boundary are counted in both chapters' "longest", so a long take can cross a chapter title without a cut.

## 3. Script rhythm — `scripts/sub-pacing.py`

```bash
python scripts/sub-pacing.py film.zh.vtt --chapters film.info.json
python scripts/sub-pacing.py film.en.vtt --gap 1.0 --edge 3
```

- Rate is reported over the full span *and* over cue time only. The second is closer to the speaker's actual delivery speed.
- CJK counts characters (Han, kana, Hangul); Latin counts words. Digits inside CJK text are not counted as words.
- `open`/`close` lines per chapter show the bridge: a close on a question (`→?`), an objection, or the thesis refrain.
- Search for callbacks: `grep -n "key phrase" film.zh.vtt` and compare the timecodes with the opening.

## 4. Sound — `scripts/audio-stats.sh`

```bash
scripts/audio-stats.sh film.mp4              # silences ≥ 0.6s below −35 dB
scripts/audio-stats.sh film.mp4 0.3 -40      # finer: catches breath pauses under music
```

- Integrated loudness (LUFS) and LRA describe the mix: VO-led essays sit around LRA 3–6 LU.
- Silence detection measures the *mix*. Under a music bed, VO pauses won't register; use subtitle gaps instead.
- A true peak above 0 dBFS in a reference means its master clips. Target ≤ −1 dBTP on your own export.

## 5. Look — `scripts/video-sheet.sh`

```bash
scripts/video-sheet.sh film.mp4 overview.jpg 0 auto 6x5 300   # whole film, 30 frames
scripts/video-sheet.sh film.mp4 open.jpg 0 1                  # first 12s, every second
scripts/video-sheet.sh film.mp4 burst.jpg 33.8 0.4            # a burst
scripts/video-sheet.sh film.mp4 take.jpg 23:12 9.2            # a 110s take, every 9.2s
```

- Default tile 400px × 4×3 gives a 1600px sheet, under the ~2000px limit many image-reading agents enforce for multi-image sessions. Keep sheets ≤ 2000px on the long side.
- Read sheets a few at a time; each covers 12 moments, so 15 sheets ≈ 180 frames, enough for a 35-min film when aimed by the metrics.
- Step choice: bursts 0.2–0.4s, boundaries 0.5–1s, long takes `length/12`.

## 6. Case-note template

```
# <title> — analysis note
SOURCE     : URL · duration · resolution/fps · codec · subtitle track used
COVERAGE   : which windows were inspected visually (list sheets), what was not
METRICS    : cuts raw/merged · ASL merged/median · bursts · longest takes
             speech rate · coverage · pauses · question lines
             LUFS · LRA · true peak · silences
STRUCTURE  : chapter table (start, length, function, ASL, bridge out)
CARDS      : T01…Tn technique cards (see SKILL.md format)
TRAPS HIT  : detector false positives found and how they were resolved
NOT KNOWN  : tools, intent, licensing of inserted media, anything undecidable from pixels
```

---
Measure everything, look where the numbers point, and write down only what transfers. Built by **[iart.ai](https://iart.ai/?utm_source=github&utm_medium=readme&utm_campaign=explainer-video-skills&utm_content=skill_footer&utm_term=reference-video-analysis)** — the AI motion agent for editable, on-brand motion graphics.
