# Studio-editable Remotion: hand-tuning after the narration

Remotion Studio (`npx remotion studio`, Remotion ≥ 4.0.475) can edit a composition on its timeline and canvas: move and trim sequences, drag keyframes, change easing, move, scale and rotate elements, edit captions. Every edit is **written back to the source code** and can be undone. Use it when the cut will be tuned by hand, typically once the real narration is recorded and the estimated timings no longer fit.

Studio only edits what it can read statically. Its server uses `@remotion/codemods` for this, and each prop reads as one of:

- **static**: a literal value, editable;
- **keyframed**: an `interpolate()` Studio understands, with editable keyframes and easing;
- **computed**: anything else, shown greyed out.

The default explainer pattern in `SKILL.md` (one timing array driving scene cuts and captions) renders correctly but reads almost entirely as computed. This file is the alternative. Everything below was measured on Remotion 4.0.542 with `@remotion/codemods`' `getNodeProps()`, and spot-checked in Studio itself.

## What Studio can read

| Code | Reads as |
|---|---|
| `<Series.Sequence name="S2" durationInFrames={930}>` | static: drag the boundary |
| `durationInFrames={DUR.s2}`, `{DUR[1]}`, `{frames(…)}` | computed |
| `<Sequence from={120}>` / `from={START.s2}` | static / computed |
| scenes from `SCENES.map((s) => <Series.Sequence …>)` | computed, one item for all |
| `interpolate(frame, [0, 30], [0, 1])` | keyframed, linear |
| … `{extrapolateRight: "clamp"}`, `{easing: Easing.bezier(.65, 0, .35, 1)}`, `Easing.in(Easing.cubic)` | keyframed |
| … `{easing: Easing.inOut(Easing.cubic)}`, `Easing.sin`, `Easing.elastic`… | computed |
| three keyframes `[0, 30, 60]` with a bezier | keyframed, one easing per segment |
| `translate: interpolate(frame, [0, 30], ["0px 0px", "600px 0px"])` | keyframed |
| `interpolate(t, …)` with `t = frame / fps`, or any variable other than `frame` | computed |
| input/output arrays from `.map()` | computed |
| the options object as a shared `const io = {…}` | computed: write it out in every call |
| `captions={[{text: "…", startMs: 0, …}]}` on an `Interactive.create()` component with `Interactive.captionsSchema` | static: the captions inspector edits it |
| `captions={imported as Caption[]}` (a JSON import) | computed |
| GSAP tweens built with `useGsapTimeline()` | not visible: Studio sees only the elements' static attributes |

### The trap: one computed start makes the rest of the scene unreadable

If any enclosing sequence's start frame is computed (a computed `from`, or a computed `durationInFrames` on an **earlier** `Series.Sequence`), every inline animation under the later sequences reads as computed too, even their literal `name`. Measured in a three-scene `Series` where only the middle duration was `{DUR.b}`: the first scene's animation stayed keyframed, the second's too, and the third read as computed throughout.

Two ways out:

1. Write every duration and `from` as a literal. `scripts/sync-scene.mjs` (below) keeps them literal when the audio changes.
2. Put each scene's animation in its own component, with its own `useCurrentFrame()`. Its keyframes then stay editable whatever the `Series` around it does, though the computed boundaries themselves cannot be dragged.

Do both for a film you mean to tune.

## Layout of a tunable film

```tsx
<Series>
  <Series.Sequence name="S0 Memes" durationInFrames={1110}>
    <Audio name="S0 narration" src={staticFile("vo/s0.wav")} />
    <SceneMemes />                                   {/* own component, own useCurrentFrame() */}
    <Captions name="S0 captions" captions={[/* written by sync-scene.mjs */]} />
  </Series.Sequence>
  <Series.Sequence name="S1 Chat box" durationInFrames={900}>
    …
  </Series.Sequence>
</Series>
```

- **Scenes**: one named `Series.Sequence` per scene. Durations are literals. No `.map()` over scenes that need their own timing.
- **Scene bodies**: separate components. Animate with `interpolate(frame, [literal frames], [literal values], {inline options})`.
- **Selectable elements**: wrap HTML elements in `Interactive.Div` (or `Interactive.create()` for a component) and give them a `name`. Keep `style` a plain inline object: no spreads, constants or arithmetic.
- **Captions**: a component wrapped with `Interactive.create({Component, schema: {...Interactive.captionsSchema}, layout: "absolute-fill"})`, with its captions passed inline.
- **GSAP props**: may stay in `useGsapTimeline()` (see **diagram-animation**). In Studio they move and trim as a block, and anything to be tuned there is better written with `interpolate()`.
- **Code Studio greys out**: hand it to Remotion's own `/remotion-interactivity` skill (`npx remotion skills add`), which restructures markup for Studio.

## From recorded narration to an editable cut

Until the narration exists, keep the timing-array pattern from `SKILL.md`: timings are estimates (words ÷ rate) and one array keeps captions and cuts in step. Once it is recorded, the audio becomes the source of truth:

```bash
# 1. word-timed captions from the recording (faster-whisper)
python <skills>/scripts/transcribe-captions.py public/vo/s2.wav public/vo/s2.captions.json --language zh
# 2. fix homophones against the script in the JSON (whisper's timings are what matter)
# 3. set the scene's length to its audio and inline its captions, as literals
node <skills>/scripts/sync-scene.mjs src/Film.tsx "S2 Memory" public/vo/s2.wav --captions public/vo/s2.captions.json --fps 30 --tail 6
# 4. check that nothing you mean to tune reads as computed
node <skills>/scripts/studio-check.mjs src/Film.tsx --strict durationInFrames,style.opacity,style.translate
# 5. tune by hand: drag boundaries and keyframes, fix caption words in the captions inspector
npx remotion studio
# 6. render and verify as in SKILL.md
```

Measured on a 5.68 s line at 30 fps with a 6-frame tail:

- `sync-scene.mjs` set the scene to 177 frames and wrote the 26 word captions inline, and both then read as static.
- The render was 6.91 s with the captions in step with the audio.
- Whisper's text had one homophone error, which step 2 exists for.

`@remotion/codemods`, which both scripts use, is a draft API. Keep it on the same version as the rest of the project's Remotion packages.

## Handing over to an editor (OpenTimelineIO)

To finish a cut in DaVinci Resolve or Premiere (25.6+), Remotion documents an agent skill, `remotion-opentimeline`. It is not part of `remotion-dev/skills`: copy it from the docs page "Export to OpenTimelineIO" into `.agents/skills/remotion-opentimeline/SKILL.md`.

- **Native clips**: media (`<Video>`, `<Audio>`, `<Img>`) becomes editable clips.
- **Rendered fallbacks**: text, shapes, `interpolate()`/`spring()` animation, effects and transitions are pre-rendered as overlays (muted ProRes 4444 over transparency) or stems.
- **Coming back**: `@remotion/codemods` ≥ 4.0.542 has `generateOpenTimelineComposition()` to turn an `.otio` back into editable TSX.

Not tested here.
