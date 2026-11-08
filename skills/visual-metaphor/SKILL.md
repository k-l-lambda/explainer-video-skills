---
name: visual-metaphor
description: This skill should be used when the user asks to "visualize an abstract concept", "find a visual metaphor for X", "make this idea concrete on screen", "design props for an explainer", "show risk/credit/latency/incentives without a stock photo", "turn an idiom into an animation", or "avoid generic b-roll in an explainer". Covers metaphor design cards, relation-first prop design, motif reuse and escalation, honest labelling, and GSAP/SVG recipes for gauges, hand-offs, loops and corrections.
version: 0.1.0
---

# Visual Metaphor Design

Explainers fail visually when they illustrate **nouns** (a photo of a bank for "bank"). They work when they animate a **relation**: who passes what to whom, what is pinned, what spins without moving. This skill turns each abstract idea into a prop plus a motion verb, keeps a small set of props recurring across the film, and labels them honestly.

## When to use

- Any explainer where the subject is abstract: finance, policy, software architecture, biology, incentives.
- Replacing stock footage / generic b-roll with props that carry the argument.
- Planning recurring visual motifs for a long-form or series explainer (see **longform-explainer**).
- Converting a figure of speech in the script into an on-screen action.

The **explainer-video** rule "one analogy per video" still applies to the *master* analogy. This skill adds the scene-level props that live inside it.

## Core principle: animate the relation, not the noun

Before drawing anything, write the sentence as **subject → verb → object** and pick a prop whose physical motion *is* that verb.

| VO line | Noun illustration (weak) | Relation prop (strong) |
|---|---|---|
| "Banks only look at collateral" | bank building | a magnifier sweeps past the person and locks onto a gold stamp |
| "Bailouts stop prices from signalling" | money pile | a gauge needle pinned by a clamp labelled "bailout", jittering, unable to move |
| "Blame passes from one actor to the next" | crowd photo | one hat handed figure → figure → figure |
| "Money circulates without reaching firms" | vault | tokens orbit four boxes in a ring; factories sit outside with a dashed, unreached line |
| "The engine runs, the car doesn't move" | — | rev counter at the redline, speedometer at zero |

Test it on mute: with the sound off, a viewer should be able to say which relation the prop shows, even without the subject.

## The metaphor card

Fill one per abstract idea before building:

```
M03  "Idling capital"
REAL THING   : deposits recycled inside the financial system
PROP         : rev counter + speedometer (one car dashboard)
MAPPING      : revs = money moving · speed = output reaching firms
MOTION VERB  : revs climb to red while speed needle stays at 0
VIEWER SEES  : effort without progress
MISLEADS IF  : viewer thinks money is literally wasted (it is lent — label "simplified")
LABEL        : "illustrative"
RECURS IN    : CH 1 (plant), CH 15 (payoff)
```

The **MISLEADS IF** line is mandatory. Every metaphor drops something. Name it, then fix it in VO or with a label.

## Where props come from

1. **Literalize the idiom already in the script.** Languages are full of physical metaphors: "idling", "safety net", "pass the buck", "red light / green light", "pawnshop". Building the idiom as a prop makes VO and picture say the same thing. This is the highest-yield source.
2. **Instruments for quantities.** Gauge, thermometer, scale, odometer, hourglass. Anything with a needle shows *a value that should move*, so pinning it is visible.
3. **Hand-offs for responsibility and risk.** A token, hat or parcel passed between figures. The holder is the bearer.
4. **Topology for flows.** Rings for circulation, chains for causality, dashed/unreached lines for what the flow misses.
5. **Documents for evidence.** Tickets, ledgers, forms. A highlighter or magnifier on the decisive word turns reading into an action.

Prop catalog with motion verbs and failure modes: `references/metaphor-catalog.md`.

## Motif economy

Use a **small cast of props** (5–8 for a long film) and give each a fixed meaning for the whole piece. Recurrence builds meaning; novelty resets it.

- **Escalate, don't replace.** One gauge in chapter 4 → three gauges, all pinned, in the resolution. The viewer reads the second appearance instantly.
- **Re-use the material, change the label.** A one-character patch on a paper title ("who to *lend* to" → "who to *invest* in") reframes without a new scene.
- **One color = one meaning.** Highlighter accent = "the word that matters"; red = alarm/failure. Never swap them mid-film.

## Diff and correction moves

Explainers often fix a misconception. Show the edit itself:

- **Strike-through + replacement**: the wrong word is crossed in red and the right one written beside it. The viewer sees *what changed*.
- **Before/after pair** in one frame, same layout, one variable different.
- **Patch**: a paper scrap pasted over one word or digit.

## Honest labelling

A metaphor is a claim about structure. Keep it from passing as data:

- Corner tag "illustrative" / "simplified" on any constructed number or flow.
- Don't put real logos on reconstructed scenes; use generic shapes or faceless figures for private/reported conversations.
- When a prop shows a quantity, either use the real value (with source) or no value at all, never a plausible-looking fake.

## Recipes

Gauge needle pinned (the needle tries to swing and is clamped back):

```js
// SVG: <g id="needle" transform-origin="200 200">…</g>, angle 0 = left, 180 = right
const tl = gsap.timeline();
tl.fromTo("#needle", { rotation: 20 }, { rotation: 150, duration: .9, ease: "power2.out" }) // free swing
  .addLabel("clamp")
  .from("#clamp", { y: -80, opacity: 0, duration: .35, ease: "back.out(2)" }, "clamp")
  .to("#needle", { rotation: 90, duration: .25, ease: "power3.in" }, "clamp+=.2")       // forced back
  .to("#needle", { rotation: "+=4", duration: .06, yoyo: true, repeat: 9, ease: "none" }); // strain jitter
```

Hand-off along an arc (a token passes between figures):

```js
gsap.registerPlugin(MotionPathPlugin);
// arcBetween(a, b) returns an SVG path arcing between two figures (defined in the catalog demo)
const hops = [["#a", "#b"], ["#b", "#c"], ["#c", "#d"]];
const tl = gsap.timeline();
hops.forEach(([from, to]) => tl.to("#hat", {
  duration: .7, ease: "power1.inOut",
  motionPath: { path: arcBetween(from, to), autoRotate: false },
}).to(to, { scale: 1.08, duration: .15, yoyo: true, repeat: 1 }, "<.55")); // receiver reacts
```

Circulation ring that never exits:

```css
.token { offset-path: path("M300 120 a180 120 0 1 1 -1 0"); animation: orbit 3s linear infinite; }
.token:nth-child(2) { animation-delay: -1s } .token:nth-child(3) { animation-delay: -2s }
.unreached { stroke-dasharray: 6 8; opacity: .45; }   /* the factory link nobody travels */
@keyframes orbit { to { offset-distance: 100%; } }
@media (prefers-reduced-motion: reduce) { .token { animation: none; } }
```

Strike-through correction:

```js
tl.fromTo("#strike", { scaleX: 0 }, { scaleX: 1, transformOrigin: "left center", duration: .3, ease: "power2.out" })
  .from("#fix", { y: 10, opacity: 0, duration: .3 }, "+=.15");
```

Full runnable versions (with the `?t=N` seek harness): `references/metaphor-catalog.md`.

## Output checklist

- Every abstract idea has a metaphor card with a motion verb and a MISLEADS IF line.
- Props show relations; no shot is a noun illustration standing in for a sentence.
- Mute test passes: each prop's relation is nameable without VO.
- A small, fixed prop cast; recurrences escalate rather than introduce new props.
- Color meanings fixed for the whole piece.
- Constructed numbers/flows labelled; no fake data; no real logos on reconstructions.

## Deliver & verify (standalone HTML)

> **Packaged helper** (`scripts/`): `scripts/seek-shot.sh metaphor.html 0 0.9 1.4 3` freezes the `?t=N` harness; `scripts/contact-sheet.sh sheet.png frame-*.png` tiles them. See `scripts/README.md`.

A single prop beat ships as **one HTML file** (inline SVG, GSAP from CDN, one master `tl`, the standard `?t=N` seek harness from **diagram-animation**). Inside a rendered film, port it to a Remotion composition and verify with `remotion still`.

**Before you finish:**
1. Frozen frames at *before*, *during* and *after* the motion verb each read on their own (e.g. needle free → clamped → straining).
2. The label ("illustrative"/"simplified") is legible in every frame where the prop carries a number or flow.
3. `prefers-reduced-motion` shows the end state (clamped needle, completed hand-off) without looping motion.
4. Opens standalone; no console errors.

## Reference files

- `references/metaphor-catalog.md` — prop catalog (relation → prop → motion verb → misleads-if), escalation patterns, idiom-to-prop worksheet, and complete runnable HTML for the pinned gauge, hand-off chain, circulation ring, magnifier lock-on and strike-through correction.
