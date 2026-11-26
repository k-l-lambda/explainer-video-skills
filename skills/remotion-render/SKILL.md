---
name: remotion-render
description: Render long Remotion films reliably and fast - verify before encoding, fix the parallel-render texture race, choose software GL vs a real GPU per scene type, split the film into chunks across browser processes or machines, reuse a previous render when only a prefix changed, and verify frame counts and seams. Use when a full render takes hours, when frames come out blank or wrong under parallel rendering, when moving a render to another machine (GPU, fonts, old C library), or when re-rendering after a small edit.
---

# Rendering long Remotion films

**explainer-video** builds the composition and checks it with stills; this skill is about the render
itself once the film is long (tens of thousands of frames, three.js scenes, pre-rendered clips). Numbers
below were measured on a 20-minute 1080p30 film (37k frames) with three.js, shader, Manim-clip and
layout shots.

## 1. Before a long render

- **Stills first** at shot boundaries and inside each hold (explainer-video, *Deliver & verify*).
- **A short slice at full settings** (a few hundred frames of the heaviest shots) tells you the real
  speed. The renderer's own ETA in the first minutes is dominated by whatever comes first and can be off
  by 2×.
- **Render the final cut with a prop**, not a code edit: e.g. `--props='{"badges":false}'` read through
  `getInputProps()` turns off debug overlays while previews keep them.
- **Render video muted and mux audio afterwards** (`--muted`, then `ffmpeg -map 0:v -map 1:a`): the mix
  is made offline, and video can then be reused while the audio changes.

## 2. Parallel rendering: the texture race

With `--concurrency` > 1, three.js scenes that load textures can render frames with blank textures
(white cards) even though single-threaded renders are fine: `continueRender` fires when the texture
object exists, before the GPU has drawn it. Fix in the component:

- load with a few retries (e.g. 4 × 250 ms) instead of failing once;
- after the texture is set, wait **two `requestAnimationFrame`s in a `useEffect`**, then `continueRender`.

Verify by rendering the same frames at concurrency 1 and N and diffing them.

## 3. Software GL or a real GPU

Headless Chrome renders WebGL either in software (`--gl=swangle`, SwiftShader on the CPU: deterministic,
works anywhere) or on a GPU (`--gl=angle-egl` on Linux with vendor EGL libraries visible to the browser,
`--chrome-mode=chrome-for-testing`).

What decides the speed:

- **One browser = one GPU process.** All tabs of a render (its `--concurrency`) share it. In software it
  is SwiftShader using ~13 cores at most; more concurrency does not help once it saturates.
- **Geometry-heavy three.js scenes**: a real GPU was **>20× faster** (a 300-frame chunk of a dense
  surface: 20–50 min in software vs 40–80 s on a GPU).
- **Scenes dominated by per-frame readback** (a modest scene re-rendered from scratch every frame) can
  be **slower** on the GPU path (155 s vs 38 s for the same 300 frames). Measure per scene type.
- **Pure layout/CSS/2D shots and pre-rendered clips**: CPU-bound either way; a GPU helps modestly.
- **Pixels**: software renders are bit-identical across machines with the same fonts; GPU renders differ
  in ~0.2 % of pixels at antialiased edges — invisible, but do not mix them where a hard cut must be
  pixel-identical.

## 4. Splitting the render

Throughput scales with the number of **browser processes**, not tabs:

- Cut the film into chunks (e.g. 300 frames), run a queue of independent `remotion render --frames=a-b`
  workers, then concatenate the chunks losslessly (`ffmpeg -f concat -c copy`; same settings → same
  stream parameters).
- **Bundle once** (`npx remotion bundle`) and render every chunk from the bundle; otherwise every worker
  re-runs webpack.
- **Stagger worker start-up** and raise `--timeout` (e.g. 180 s): many browsers initialising at once
  exceeded the 30 s default ("Timeout exceeded rendering the component initially").
- **Find the worker count by measuring, and expect a cliff**: 4 workers on one machine scaled linearly
  (4 GPU workers sharing one GPU: 37 s per 300-frame chunk, ~32 fps in aggregate); 8 workers collapsed
  ~10× (software and GPU alike). Pinning workers to CPU subsets made it worse. Start at 4 and measure.
- **Dynamic queue, not static ranges**: shot cost varies by 20× along a film; a static split leaves
  workers idle at the end. Send the known heavy chunks to the fastest path (GPU) early.
- **Never trust a fast finish**: check that each chunk file exists and has the right frame count; one
  "42 s" chunk in testing was a silent failure.

### If you have more machines or GPUs

If a machine with several GPUs (or many cores) is available, the same chunk queue runs there: sync the
project **without** audio (only what video frames read), install dependencies, bundle there, render
chunks, fetch the concatenated result. Things that broke on a different machine:

- **Fonts**: missing CJK fonts render as boxes; sync the fonts the film uses into the user font directory
  and rebuild the cache, then diff a still against a local one (expect 0 difference in software GL).
- **An older C library** than the compositor binary requires: `remotion render` warns, stills may work,
  but video fails (`GLIBC_2.35 not found`). Without root, unpack a newer libc next to the project, put the
  compositor behind a wrapper that runs it through that libc's dynamic loader with `--library-path`, and
  pass `--binaries-directory`.
- **A browser** may have to be supplied (`--browser-executable`), with `--chrome-mode=chrome-for-testing`
  for a full Chrome.
- **Static files through nested symlinks** may 404 in the bundle's server; use real files or hard links.

## 5. Reusing a previous render

Re-rendering everything after a small edit is rarely necessary:

1. **Diff the old and new timelines shot by shot.** If every shot from some point on has the same length
   and the same start shift, frames there are the same frames, shifted.
2. **Prove it**: render a handful of new frames (one per chapter, including heavy shots) and compare with
   the old render's frame at `new − shift`. Expect only encoding noise (mean difference ~3/255, no
   element added or missing).
3. **Cut at a keyframe of the old render** inside a shot, away from transitions
   (`ffprobe -show_entries packet=pts_time,flags`; Remotion's x264 output had one every 250 frames).
4. Render only the new head up to that frame, take the old tail from that keyframe with `-c copy`, concat,
   mux the new mix. Check: total frame count equals the timeline's; frame-to-frame difference at the seam
   is in line with its neighbours.

A film whose head changed (a title sequence inserted, an opening re-timed) was rebuilt this way in minutes
instead of a full multi-hour render.

## 6. Shell and job hygiene

- **`pkill -f PATTERN` over ssh kills the ssh session** when PATTERN appears in its own command line. Put
  kill logic in a script file and call the file.
- **Keep previews small and comparable**: reduced scale, debug badges on, the matching slice of the full
  mix, absolute paths in concat lists (relative paths resolve against the list's directory).
- **Note what each render used**: timeline version, mix version, props. A render made before a timeline
  change is only reusable through §5.
