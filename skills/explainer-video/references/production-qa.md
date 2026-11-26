# Production QA: layout, captions, shot joins, timeline

Rules learned building a 20-minute, 88-shot narrated math explainer in Remotion (three.js, Manim clips,
generated stills and clips, TTS narration, a bed per chapter). They hold for short pieces too; long
films just hit every one of them. **SKILL.md** has the pipeline; this file is what to check while
building and before rendering.

## 1. Layout: reserve the zones, then check overlaps

Decide the reserved zones once, in the theme, before the first scene is built:

| Zone | What lives there | Rule |
|---|---|---|
| Caption band | burned captions, bottom ~15 % | No scene content ever enters it. Labels, formulas and annotations stop above it. |
| Navigation strip | chapter/station icons, if the film has one | Fixed width on one edge; scene content keeps a gutter from it. |
| Debug badge | shot id + source tool, top right | On for previews, off for the final cut (a render prop, not a code edit). |
| Title-safe | ~5 % inset all round | Text inside it; only backgrounds bleed. |

Overlaps that actually happened, and the rule each one produced:

- **Labels on a moving 3D object** (zeros on a rotating surface) drifted into the caption band and into
  each other. Re-project labels every frame and give each a fallback side: if its box would cross the
  caption band or a neighbour, put it on the other side of its anchor; fade labels out during the fastest
  part of a camera move rather than letting them collide.
- **Two annotation groups** (a formula and its gloss, a label and a callout) placed independently in
  adjacent beats ended up on top of each other once timings moved. Lay out every element that can be on
  screen at the same time in one place, not per beat.
- **Big display type over content** is allowed only when intended (a title slammed over cards); give it
  a dark outline or shadow so it reads over anything.

**Check overlaps by looking at frames, systematically.** Render key frames per shot (a few inside each
hold, more where things move; ≤6 per shot keeps an 88-shot film reviewable), tile them into contact
sheets per chapter, and review every sheet. Worth automating where the layout is data: collect every
text box per frame and test pairwise intersection and intersection with the reserved zones.

## 2. Captions

SKILL.md allows ≤2 lines; on a phone, and for CJK, **one line** reads better:

- One line per caption, split at punctuation; drop trailing commas, colons and full stops; keep
  quotation marks balanced per segment (close at a cut, reopen on the next segment).
- Time each segment from **word timestamps** of the recorded narration (it starts when its first
  character is spoken), but take the **text from the script**, never from the transcript: ASR mishears
  homophones and polyphones, the script does not.
- Captions are a reserved zone (above), so they never need to dodge content.

## 3. Joining shots

Treat a cut as a property of the **pair** of shots, not of either shot.

- **Decide per pair**: hard cut, full-frame push (pan), dissolve, or a bespoke move. Keep a table of
  pair → transition; the default is the one the style system chose.
- **Pushes move the whole frame**: out of the viewport and the next shot in, with ease-in-out. A push
  that moves a fraction of the frame reads as a glitch. Derive the direction from the pair so the
  outgoing and incoming shots agree.
- **The outgoing shot keeps playing** during the overlap. Give each shot's sequence its length plus the
  transition tail; never freeze it. Pre-rendered clips must **hold their last frame** for the tail
  (a frozen copy in a sequence that starts at the clip's end), otherwise they go blank mid-transition.
- **Nothing changed between two shots → hard cut**, and make it invisible: draw the shared elements with
  the same components and the same final state, and verify by diffing the last frame of A against the
  first frame of B (0 differing pixels outside the caption band).
- **Shared backgrounds live outside the shots.** A paper or grid background drawn inside each shot jumps
  or slides at every transition; hoist it to the film level.
- **Fades fit inside the material's own length.** If a still must fade, the fade takes the last ~30 % of
  its time; it does not extend the timeline. Keep it alive while it fades (still growing or drifting),
  so it does not look stopped.
- **Use a real video's frame when crossing into it**: to fade into a generated clip, hold its first frame
  for a few frames before its cut (e.g. 4–8 frames) and dissolve over the outgoing shot.

## 4. Timeline driven by the recorded narration

- The narration's measured durations define the timeline; shot lengths and beats derive from them.
  Store **holds** (extra silence for an animation) keyed by the opening words of the line they belong to,
  not by line ids, so edits to the script do not move them. Anchors such as "this shot starts N s after
  that line ends" keep inserted material (a title sequence, a silent montage) data-driven.
- **Re-recording one line must not move the film**: pad the new take with silence, or trim leading and
  trailing silence, to the old duration; if speech would have to be cut, try another take.
- **Re-timing checklist** (when a line moves to another shot, or a hold changes):
  1. List every visual cue anchored to words of the moved line (a montage on one word, a highlight on
     another). Move each cue with its words, or re-anchor it on purpose. A cue left behind becomes an
     orphan that plays silent somewhere else.
  2. Look at every gap between consecutive lines after the change; a hold that served the old layout can
     leave a dead gap in the new one.
  3. Check that animations still fit: a shot that lost seconds may cut an animation short, a shot that
     gained them needs something alive on screen.
  4. Rebuild timeline, timing, generated data and the audio mix in one pass; spot-check captions after the
     change point.
- When only a prefix of the film changed and everything after it shifted by a constant, the rest of a
  previous render can be reused (**remotion-render**).

## 5. Previews

- Render previews at reduced scale with debug badges on, for a stretch that includes one shot before
  and after the change, and mux the matching slice of the full mix so voice, bed and cues are heard as
  in the film.
- When a preview goes to a chat app with an upload limit, re-encode to fit rather than trimming content.
