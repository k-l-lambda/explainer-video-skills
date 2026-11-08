---
name: canvas-camera-animation
description: This skill should be used when the user asks to "move a camera across a 2D scene", "pan and zoom through an infinite canvas", "build a paper-collage documentary look", "add parallax and fake depth of field to flat art", "do a whip-pan transition", "make one continuous shot through an explainer", "Ken Burns a document", or "make 2D motion graphics feel cinematic". Covers world/station layout, camera grammar (push, pull, follow, whip, hold), parallax and DOF layers, velocity motion blur, and tactile material systems, in GSAP and Remotion.
version: 0.1.0
---

# Canvas Camera Animation

Lay the whole argument out as **one large 2D world** and move a virtual camera through it. Camera moves become the transitions: a pan follows a causal chain, a push-in isolates the decisive word, a pull-out reveals the system around a detail. This gives flat motion graphics continuity and a cinematic feel without 3D. Hard cuts are kept for changes of source (footage, a new world).

## When to use

- Explainers with chains of causes, timelines or document trails that read better as a journey than as slides.
- A paper/collage/archival documentary look: cut-outs, halftone, grain, typed labels.
- Any 2D scene that needs depth: parallax, focus pulls, motion blur.
- Long mechanism chapters that should run as one continuous move (see **longform-explainer**).

Props come from **visual-metaphor**; charts and node graphs from **diagram-animation**; an actual 3D world from **isometric-animation** (Three.js) when space itself is the subject.

## Core principle: every move carries information

If removing a camera move loses no information, cut it. Map each move type to a meaning and keep the mapping for the whole piece:

| Move | Means | Typical use |
|---|---|---|
| Push-in | focus: "this detail decides it" | a date on a document, one word, a stamp |
| Pull-out | context: "this is part of something bigger" | price tag → crowd of persona cards |
| Pan / track | sequence or causality: "this leads to that" | along a timeline, link to link of a chain |
| Follow | flow: "watch where it goes" | a token travelling between boxes |
| Whip (blurred pan) | jump in time/place within the same world | year → year, case → case |
| Hold | weight: "let this land" | counter-argument, a number, a quote |
| Hard cut / flash | change of source | to footage, to a dramatized scene |

Measured case: in a 35-minute paper-collage essay, two mechanism chapters ran 60+ seconds with **zero hard cuts**, the camera moving through one continuous canvas, while the cold open cut about every 4 seconds. A burst of ~30 detector "cuts" in the opening turned out to be whip-pans: motion blur fools scene detection (see **reference-video-analysis**).

## World layout: stations on a board

Design the world before the camera:

1. List the **stations** (one idea each) in VO order.
2. Place them so the **reading direction is the logic**: left → right for time and causation, top → bottom for drilling into detail, outward for zooming to context.
3. Give each station a **frame**: the camera rectangle (x, y, zoom) where that idea reads at full size.
4. Leave connective material between stations (threads, arrows, timeline ticks) so pans pass *through* meaning, not empty paper.
5. Nest detail inside stations for push-ins: the decisive word sits in the document at real scale, readable only at 4–8× zoom.

```
STATION  frame (x, y, zoom)   VO cue                 move in      hold
S1       (0, 0, 1)            "Ask anyone…"          —            1.2s
S2       (1400, 0, 1)         "…but the numbers say" pan right    1.0s
S2a      (1630, 120, 6)       "…165 trillion"        push-in      1.5s
S3       (1400, 0, .35)       "…in a world where"    pull-out     0.8s
```

## Camera rig

Drive one `world` transform from a camera `{x, y, zoom, rot}`. The camera looks at world point (x, y), so the world is translated by the negative and scaled around the viewport center.

```js
// world: <div id="world"> containing all stations, positioned in world px
function applyCamera(cam, vw, vh) {
  world.style.transform =
    `translate(${vw/2}px, ${vh/2}px) scale(${cam.zoom}) rotate(${cam.rot||0}deg) translate(${-cam.x}px, ${-cam.y}px)`;
}
```

- **Interpolate zoom in log space** (`zoom = exp(lerp(ln z0, ln z1, t))`). Linear zoom looks like it accelerates as it gets closer.
- **Ease every move** (`power2.inOut` / `easeInOutCubic`), 0.8–1.6s for a pan, 0.6–1.0s for a push. Whips are 0.25–0.4s.
- **Arrive before the word.** The camera settles ~0.2s before the VO stresses the station's key word; never land mid-word.
- **Don't move during a number.** Hold still while a figure counts up or a quote is read.
- **Push-in on a far station = pull out a bit, travel, push in** (a "hop"). Flying at high zoom across the board is disorienting.

Full GSAP and Remotion rigs, log-zoom, hops, and path cameras: `references/camera-recipes.md`.

## Depth on a flat board

- **Parallax layers.** 3–4 layers (backdrop paper, mid props, foreground cut-outs, overlay grain). Each layer gets a factor `p`; translate by `-cam.x * p`. Foreground `p > 1`, backdrop `p < 1`. Keep the station layer at `p = 1` so frames stay exact.
- **Fake depth of field.** Blur layers by their distance from the focus layer: `blur = k * |p - p_focus|`. Animate `p_focus` for a focus pull (resume blurred behind, quote sharp).
- **Cut-out shadows.** A soft offset shadow under every paper element (`drop-shadow(4px 6px 6px rgba(0,0,0,.25))`) is most of the "physical" look. One light direction for the whole film.
- **Velocity motion blur.** Blur along the motion direction proportional to camera speed; whips get strong blur, slow pans none. In Remotion, wrap with `@remotion/motion-blur`'s `<CameraMotionBlur>`; on the web, an SVG `feGaussianBlur` with `stdDeviation="${vx*k} 0"`.

## Material system (lock before building)

Choose one tactile system and keep it everywhere. Its rules are part of the style system (see **explainer-video** style-system spec):

```
BASE       : off-white paper with fibre grain; optional grid cutting mat behind
FIGURES    : halftone / engraving-style cut-outs, slight rotation (±2°), soft shadow
TYPE       : heavy serif display + typewriter body; text types on, letter by letter
ACCENT     : one highlighter colour = "the word that matters"; one red = alarm/failure
FOOTAGE    : framed like a print, graded toward the paper palette, grain kept
TRANSITION : whip within the board · white flash into dramatized scenes · hard cut to footage
```

Alternatives with the same mechanics: blueprint (cyan lines, grid, stencil type), chalkboard, risograph (2–3 spot colours, misregistration), newsprint. Texture and shader recipes: `references/material-systems.md`.

## Transitions inside the world

- **Morph handoff**: the last prop of a station becomes the first of the next (a price tag pulls out into a grid of cards).
- **Typewriter wipe**: a new heading types on over the current frame, then the camera moves to it.
- **Patch**: paste a paper scrap over one word to change the claim (useful for the frame shift at the end of a film).
- **Flash white** (2–4 frames) to enter a dramatized or stylized scene, so the change of reality register is felt.
- **Match-shape cut**: cut to footage on a shape that matches the board (a circle stamp → a coin).

## Output checklist

- Every move maps to a meaning from the move table; no decorative drifting.
- Stations laid out so reading direction = logic; connective material between them.
- Camera arrives before the stressed word and holds during numbers/quotes.
- Zoom interpolated in log space; far jumps use a hop, not a high-zoom fly.
- 3–4 parallax layers, one light direction, consistent shadow and grain.
- Whips carry blur proportional to speed; slow moves are sharp.
- Hard cuts only for source changes; dramatized scenes entered with a distinct transition.
- `prefers-reduced-motion`: replace moves with cross-fades between station frames.

## Deliver & verify

> **Packaged helper** (`scripts/`): `scripts/seek-shot.sh canvas.html 0 0.6 1.2 2.4` freezes the `?t=N` harness; `scripts/contact-sheet.sh` tiles them. For a rendered video, `scripts/video-sheet.sh out.mp4 sheet.jpg 0 0.5` shows every half-second. See `scripts/README.md`.

Standalone scene: **one HTML file**, one master GSAP timeline that animates the camera object and calls `applyCamera` `onUpdate`, plus the `?t=N` seek harness (as in **diagram-animation**). Film: a Remotion composition that computes the camera from `useCurrentFrame()`.

**Verify — freeze at stations *and* mid-move:**
1. At every station frame the content is centred, fully legible and nothing is clipped.
2. Mid-move frames: blur only on fast moves; no tearing at layer edges; parallax layers don't reveal the edge of the board.
3. Push-in end frames: the decisive word is sharp at the final zoom (author text as SVG/DOM, not a raster, so it survives 8×).
4. Reduced-motion path shows each station without the moves.

## Reference files

- `references/camera-recipes.md` — complete runnable camera rig (GSAP + seek harness) with stations, log-zoom, hops, parallax layers, focus pull and velocity blur; Remotion port with `interpolate` keyframes and `<CameraMotionBlur>`; whip-pan recipe; path-following camera.
- `references/material-systems.md` — paper grain via SVG `feTurbulence`, halftone via CSS gradients and SVG masks, torn edges, cut-out shadows, highlighter swipes, typewriter text, footage grading (CSS filters and `ffmpeg`), and alternative material sets.
