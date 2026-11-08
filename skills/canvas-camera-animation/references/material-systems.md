# Material Systems — Cookbook

A material system is the set of physical rules your 2D world obeys: what it's made of, how light falls on it, how text arrives. Lock it once and every station, prop and transition will look like part of the same object.

## 1. Spec sheet (fill before building)

```
BASE        : surface + texture + backdrop        e.g. off-white paper, fibre grain, green cutting-mat grid
ELEMENTS    : how props are made                 e.g. cut-out paper, halftone/engraving fills, ±2° rotation
LIGHT       : one direction, one shadow          e.g. top-left, 4px 6px 10px rgba(0,0,0,.3)
TYPE        : display + body + arrival           e.g. heavy serif / typewriter mono / types on letter by letter
ACCENTS     : ≤ 2 colours with fixed meaning     e.g. cyan highlighter = key word · red = alarm/failure
FOOTAGE     : how real media is framed            e.g. printed photo with border, graded warm, grain kept
GRAIN       : one grain amount over everything    e.g. 4–6% luminance noise overlay
```

## 2. Paper grain (SVG noise, no images)

```html
<svg width="0" height="0" style="position:absolute">
  <filter id="paper">
    <feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="7" result="n"/>
    <feColorMatrix in="n" type="saturate" values="0" result="g"/>
    <feComponentTransfer in="g"><feFuncA type="linear" slope=".08"/></feComponentTransfer>
    <feComposite in2="SourceGraphic" operator="in"/>
    <feBlend in="SourceGraphic" mode="multiply"/>
  </filter>
</svg>
<div class="card" style="filter:url(#paper)">…</div>
```

For a whole-frame grain overlay, render one full-screen `<div>` with the noise as its background and `mix-blend-mode: multiply; opacity: .5`. In video, shift its `seed` (or offset) every 2–3 frames so grain *moves* like film instead of sitting on the screen.

## 3. Halftone fills

CSS dot screen over an image or shape:

```css
.halftone {
  background: radial-gradient(circle, #1d1d1b 32%, transparent 34%) 0 0 / 6px 6px;
  -webkit-mask: url(portrait.png) center / cover;  mask: url(portrait.png) center / cover;
}
```

True tonal halftone (dot size follows image brightness): run the source through `ffmpeg` / ImageMagick offline (`magick in.png -colorspace gray -ordered-dither h6x6a out.png`) and use the result as the cut-out. Engraving-style art (line hatching) is a stronger "archival" signal than dots; keep one of the two per film.

## 4. Torn and cut edges

```css
.torn { clip-path: polygon(0 3%, 6% 0, 14% 2%, 23% 0, 31% 3%, 42% 1%, 55% 3%, 63% 0, 74% 2%, 86% 0, 94% 3%, 100% 1%,
                            100% 97%, 92% 100%, 81% 98%, 70% 100%, 58% 97%, 46% 100%, 33% 98%, 21% 100%, 9% 97%, 0 100%); }
.cutout { filter: drop-shadow(4px 6px 6px rgba(0,0,0,.28)); transform: rotate(-1.5deg); }
```

Generate the polygon once per element with a seeded random so it's stable across renders. Never use `Math.random()` at render time in Remotion.

## 5. Highlighter swipe (synced to the stressed word)

```css
.hl { background: linear-gradient(#21b8c6, #21b8c6) no-repeat 0 88% / var(--hl, 0%) 42%; }
```

```js
// drive --hl from the master clock; land 100% on the VO's stressed syllable
el.style.setProperty("--hl", `${100 * clamp01((t - tWord + .3) / .3)}%`);
```

Variations: a scribbled circle (SVG path draw-on, see **whiteboard-animation**), an underline that overshoots the word slightly, a red strike-through for corrections (see **visual-metaphor**).

## 6. Typewriter text

```js
function typed(text, t, t0, cps = 18) {             // characters per second
  const n = Math.max(0, Math.floor((t - t0) * cps));
  return text.slice(0, n) + (n < text.length && Math.floor(t * 2) % 2 ? "▍" : "");
}
```

Pace the typing so the heading completes ~0.2s before the VO says it. For CJK headings, 8–12 chars/s reads as deliberate; for Latin, 15–25 chars/s. A tiny random vertical jitter per glyph (seeded, ±0.5px) sells the mechanical feel.

## 7. Footage inside the world

Grade footage toward the paper palette but keep it recognisably footage.

```css
.footage { filter: sepia(.35) saturate(.75) contrast(1.05) brightness(.97);
           border: 10px solid #efe9dc; box-shadow: 4px 6px 10px rgba(0,0,0,.3); }
```

Offline (baked) grade + vignette + grain:

```bash
ffmpeg -i clip.mp4 -vf "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=saturation=.8:contrast=1.05,vignette=PI/5,noise=alls=8:allf=t" -c:a copy clip-graded.mp4
```

Blend the sepia matrix at partial strength (or mix with the original) for a lighter grade. Always caption footage with source and date, because it is evidence (see **longform-explainer**).

## 8. Alternative material sets

| System | Base | Elements | Type | Accent |
|---|---|---|---|---|
| Paper archive | off-white paper, grid mat | cut-outs, halftone, engraving | heavy serif + typewriter | 1 highlighter + red |
| Blueprint | deep blue, white grid | cyan line art, dimension lines | stencil / technical mono | white + amber |
| Chalkboard | slate, chalk dust | chalk strokes (draw-on) | handwritten | yellow chalk |
| Risograph | cream stock | 2–3 spot colours, misregistration | bold grotesk | the spot colours |
| Newsprint | grey newsprint, columns | halftone photos, rules | condensed headline serif | red stamp |

Mechanics (camera, parallax, highlighter, typing) stay identical; only the spec sheet changes.

---
Pick the material, write its rules down, and every new prop already knows how to look. Built by **[iart.ai](https://iart.ai/?utm_source=github&utm_medium=readme&utm_campaign=explainer-video-skills&utm_content=skill_footer&utm_term=canvas-camera-animation)** — the AI motion agent for editable, on-brand motion graphics.
