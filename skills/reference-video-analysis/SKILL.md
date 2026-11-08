---
name: reference-video-analysis
description: This skill should be used when the user asks to "analyze this reference video", "break down how this explainer is made", "learn the style of this video", "reverse-engineer pacing/editing/camera of a film", "extract reusable techniques from a YouTube video", "make a shot list / contact sheet from a video", or "measure cut rhythm, speech rate or loudness". Covers acquisition, measurement (cuts, ASL, speech rate, silences, LUFS), metric-guided visual review, false-positive traps, technique cards, and the observed-vs-inferred discipline.
version: 0.1.0
---

# Reference Video Analysis

Learn *how* a film works without copying *what* it is. Measure it first so you know where to look, then look closely at those spots and write down transferable techniques. Each technique card separates what you saw from what you guessed. The output feeds the other skills: structure into **longform-explainer** / **explainer-video**, props into **visual-metaphor**, moves and materials into **canvas-camera-animation**.

## When to use

- Someone shares a video and says "make ours like this" or "what makes this work?"
- Building a style guide, pacing target or shot grammar from existing work.
- Checking your own render against a reference (same metrics, side by side).

## Core principle: numbers point, eyes confirm

A 35-minute film is about 64,000 frames. You can't look at all of them, and a fixed sample every N seconds will miss sub-second events. So:

1. **Measure** the whole film cheaply (cuts, speech, audio).
2. **Rank** the anomalies: the fastest burst, the longest take, the pauses, chapter boundaries, the first 60 seconds.
3. **Look** at dense contact sheets of exactly those windows.
4. **Write** each pattern as a technique card, with timecodes as evidence.

## Pipeline

| Step | Tool | Output |
|---|---|---|
| Acquire | `yt-dlp` (video + subs + `.info.json` with chapters) | local copy for analysis only |
| Overview | `scripts/video-sheet.sh film.mp4 all.jpg 0 auto 6x5 300` | 30-frame whole-film sheet |
| Cut rhythm | `python scripts/shot-stats.py film.mp4 --chapters film.info.json` | cuts, ASL, bursts, long takes, per chapter |
| Script rhythm | `python scripts/sub-pacing.py film.vtt --chapters film.info.json` | speech rate, coverage, pauses, questions, chapter open/close lines |
| Sound | `scripts/audio-stats.sh film.mp4` | LUFS, LRA, true peak, silences |
| Targeted look | `scripts/video-sheet.sh film.mp4 w.jpg <start> <step>` | 12-frame timestamped sheet per window |
| Synthesis | technique cards + case note | reusable rules, each with evidence |

Commands, flags and the case-note template: `references/analysis-recipes.md`.

### Where to point the sheets

- **First 60s** at 0.5–1s steps: the hook structure, title placement, host entry.
- **Each chapter boundary** ±6s: how the bridge is staged.
- **Every burst** from shot-stats at 0.2–0.4s steps.
- **The longest takes** at 2–5s steps: static hold or one continuous camera move?
- **Pauses** from sub-pacing/audio-stats: what the picture does while the VO rests.
- **Callbacks**: search the subtitles for the opening line's key phrase later in the film.

## Traps (each one seen in practice)

| Signal | Naive reading | What it often is | How to check |
|---|---|---|---|
| Cluster of ~30 cuts in 5s | frantic montage | whip-pans / motion blur / white flash fooling scene detection | 0.4s-step sheet over the burst |
| 60s with zero cuts | static, slow chapter | one continuous camera move across a canvas | 5s-step sheet: is the framing changing? |
| Low ASL in a chapter | energetic editing | many small typographic swaps on one layout | sheet: same background across "cuts"? |
| High coverage (85%) | wall-to-wall talking | yes, but check where the few pauses sit | audio-stats silences → sheet at each |
| Stylized deep-focus scene | "they used 3D" | could be 2.5D collage, AI, or 3D: undecidable from pixels | record as "depth-styled scene", not a tool |
| Burst inside news footage | fast edit | handheld shake, someone walking past the lens | sheet: same shot before and after? |
| Long take across a chapter boundary | chapter starts with a cut | title card typed in during one move | sheet around the chapter start |
| Auto-captions | the script | rolling duplicates, missing punctuation | merge duplicates; use manual subs if offered |

When a metric and the sheet disagree, the sheet wins. Write down why the metric was fooled.

## Observed / inferred / extension

Every statement in the analysis gets one of three tags:

- **Observed**: visible or measurable, with timecode ("33.8–38.2s: horizontal whip blur between banquet tableaux").
- **Inferred**: a reasonable reading of the evidence, stated as such ("likely a virtual camera over a flat collage").
- **Extension**: your idea for using the technique, not in the reference.

Never state production tools, budgets or intent as facts. A frame can't show which software made it.

## Technique cards

The deliverable is a set of cards, not a frame-by-frame transcript:

```
T07  Continuous canvas for mechanism chapters                         [observed]
EVIDENCE  : 20:11–21:15 and 23:59–25:02, 0 hard cuts in 64s / 63s; sheet f1255 shows framing
            travelling across one paper board (hat passed figure → figure, drawer pulled out)
RULE      : When a chapter explains one mechanism, keep it on one board and let camera moves
            replace cuts; cut only to change source.
WHY       : continuity of space = continuity of argument; viewer never re-orients
APPLIES TO: any causal-chain explanation ≥ 30s
SKILL     : canvas-camera-animation (camera grammar) · longform-explainer (pacing by function)
DON'T COPY: the paper/grid look, the mascot, the props as drawn
```

Aim for 10–20 cards, grouped by structure, script, visual metaphor, camera/edit, material, sound, evidence. A worked set from a 35-minute essay is in `references/case-study-longform-essay.md`.

## Boundaries

- The local copy is for analysis. Don't republish frames, audio or captions from it; extracted sheets stay in a scratch folder.
- Don't copy identity assets: logos, mascots, character designs, title cards, music, signature typography or color combinations, recurring catchphrases.
- Don't inherit the reference's factual or political claims. If you reuse a fact, verify it from a primary source.
- Abstract to the principle. "Pin a gauge needle to show a suppressed signal" transfers; "a cyan highlighter on beige paper over a green grid" is a look. Use it only as a starting point for your own material system.

## Verify your own film against the reference

Run the same three measurements on your render and compare in one table:

```bash
python scripts/shot-stats.py out/ep.mp4 --chapters chapters.tsv --json mine.json
python scripts/sub-pacing.py out/ep.vtt --chapters chapters.tsv
scripts/audio-stats.sh out/ep.mp4
```

| Metric | Reference | Ours | Intent |
|---|---|---|---|
| ASL (cold open, bursts merged) | 4.1s | | ≈ match |
| Longest mechanism take | 64s | | continuous move |
| Speech rate | 4.95 chars/s | | ±10% |
| Coverage | 83.5% | | 75–90% |
| Integrated loudness | −17.2 LUFS | | platform target |

Matching numbers aren't the goal. Deviations should be deliberate.

## Output checklist

- Overview sheet + metric summaries saved with the case note.
- Every burst, longest take and chapter boundary visually checked; detector false positives noted.
- Each claim tagged observed / inferred / extension, with timecodes for observed ones.
- 10–20 technique cards, each with RULE, WHY, target skill and DON'T COPY.
- No tool/intent claims stated as fact; no identity assets carried over.
- Scratch frames kept out of the deliverable repo; the copy is used for analysis only.

## Reference files

- `references/analysis-recipes.md` — `yt-dlp` acquisition, ffmpeg scene detection and thresholds, burst merging, subtitle parsing quirks, ebur128/silencedetect, sheet sizing for image-reading agents, chapters TSV format, and a case-note template.
- `references/case-study-longform-essay.md` — measurements and 16 technique cards from a 35-minute, 18-chapter paper-collage explainer essay (structure, script, metaphor, camera, material, sound), each traced to timecoded evidence.
