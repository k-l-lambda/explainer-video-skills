# Metaphor Catalog — Cookbook

Relation-first props, how they move, and how they mislead. Then a runnable demo with the seek harness.

## 1. Prop catalog

| Relation | Prop | Motion verb | Misleads if… | Fix |
|---|---|---|---|---|
| A value is held fixed by force | gauge + clamp | needle swings, clamp drops, needle strains | the value is shown as a precise reading | no numbers on the dial, label "illustrative" |
| A signal is distorted | price tag / meter | digits flicker, settle on a wrong value | viewer assumes the true value is known | show "?" or a range for the true value |
| Effort without progress | rev counter + speedometer | revs to red, speed stays at 0 | "wasted" read literally | VO says where the motion actually goes |
| Circulation inside a closed set | ring of boxes + orbiting tokens | tokens orbit; dashed link to outside never lit | all flow appears closed | show a thin real outflow if one exists |
| Responsibility / risk transfer | hat, parcel, hot potato | passed figure → figure, receiver reacts | transfer looks voluntary | show who pushes vs who receives |
| Selection by one criterion | magnifier / sieve | sweeps past people, locks on one stamp | criterion looks like the only one | add the ignored criteria, greyed out |
| Causal chain | chain links / dominoes | camera follows link to link | chain looks deterministic | break one link to show contingency |
| One failure, system intact | drawer pulled from a cabinet | one drawer slides out, cabinet stays | failure looks costless | show the drawer's contents spilling |
| Leverage / imbalance | seesaw / scale | small weight lifts large pile | physical ratio read as exact | label "not to scale" |
| Power law | row of bulbs | most flicker out, one grows huge | survivors look predictable | randomize which bulb wins on replay |
| Rule known before vs after | traffic light | light changes at the moment the VO names it | rule looks binary | add the amber phase if the rule is fuzzy |
| Accumulating stock | odometer / debt clock | digits roll, red past a threshold | growth looks smooth | mark the dated real values on the roll |
| Erosion over time | note/IOU fading | printed value fades as years tick | rate looks constant | fade by the actual curve |
| Shock | ECG / seismograph line | flat → spike on the stressed word | single spike = single cause | stack spikes if causes are multiple |
| Misconception corrected | strike-through + rewrite | red line crosses word, new word writes in | — | keep the struck word legible |
| Small change, big meaning | paper patch over one word | scrap lands, one word changes | — | hold long enough to read both |
| A role, not a person | hat / badge on a faceless figure | badge swaps to change role | real person implied | keep figures generic |

## 2. Idiom-to-prop worksheet

1. Highlight every figurative phrase in the VO draft ("idling", "safety net", "kick the can", "pass the buck", "red light", "pawnshop").
2. For each, ask: is the figure *the point of the line*? If yes, it is a prop candidate.
3. Write the literal physical action. "Kick the can" means a can moves forward and nothing is solved, so the can lands back at the kicker's feet.
4. Check that the prop survives the mute test.
5. Keep the 5–8 strongest for the whole film; the rest stay verbal.

## 3. Escalation patterns

- **Count up**: one instance → three instances, all in the same failure state (one pinned gauge → three pinned gauges).
- **Scale up**: the same prop, bigger and closer, at the climax.
- **State change**: the prop finally moves free in the resolution (the clamp is removed).
- **Label change**: identical layout, one word patched (frame shift).
- **Context pull-out**: the prop is revealed as one element in a larger collage.

## 4. Runnable demo — pinned gauge + hand-off + correction

One file, one master timeline, `?t=N` seek harness. Freeze it at 0, 0.9, 1.6, 2.5 and 5.5 to check each state.

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>Metaphor props</title>
<style>
  body{margin:0;background:#efe9dc;font:600 20px/1.2 Georgia,serif;color:#1d1d1b}
  svg{display:block;width:100vw;height:100vh}
  .tag{font:italic 13px Georgia,serif;fill:#6b665c}
  .hl{fill:#21b8c6}
  @media (prefers-reduced-motion: reduce){ .anim{animation:none!important} }
</style></head>
<body>
<svg viewBox="0 0 960 540">
  <!-- Gauge -->
  <g transform="translate(240 300)">
    <path d="M-150 0 A150 150 0 0 1 150 0" fill="none" stroke="#1d1d1b" stroke-width="6"/>
    <path d="M60 -138 A150 150 0 0 1 150 0" fill="none" stroke="#c8392b" stroke-width="10"/>
    <g id="needle"><line x1="0" y1="0" x2="-130" y2="0" stroke="#1d1d1b" stroke-width="6" stroke-linecap="round"/></g>
    <circle r="12" fill="#1d1d1b"/>
    <g id="clamp"><rect x="-42" y="-170" width="84" height="34" fill="#c8392b"/>
      <text y="-148" text-anchor="middle" fill="#fff" font-size="13">BAILOUT</text></g>
    <text y="40" text-anchor="middle">price signal</text>
    <text class="tag" x="150" y="40" text-anchor="end">illustrative</text>
  </g>
  <!-- Hand-off -->
  <g id="figs" fill="#1d1d1b">
    <circle id="a" cx="560" cy="300" r="22"/><circle id="b" cx="680" cy="300" r="22"/><circle id="c" cx="800" cy="300" r="22"/>
  </g>
  <path id="hat" d="M-22 0 h44 l-8 -18 h-28 z" fill="#c8392b" transform="translate(560 272)"/>
  <!-- Correction -->
  <text x="560" y="420">money is <tspan id="wrong">wasted</tspan> <tspan id="fix" class="hl">recycled</tspan></text>
  <rect id="strike" height="4" fill="#c8392b"/>
</svg>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/MotionPathPlugin.min.js"></script>
<script>
  gsap.registerPlugin(MotionPathPlugin);
  const P = id => { const c = document.getElementById(id); return [+c.getAttribute("cx"), +c.getAttribute("cy") - 28]; };
  // quadratic arc from one figure's head to the next
  const arcBetween = (f, t) => { const [x1,y1]=P(f), [x2,y2]=P(t); return `M${x1} ${y1} Q${(x1+x2)/2} ${y1-90} ${x2} ${y2}`; };

  // size the strike-through from the real word box, so it fits whatever font renders
  const bb = document.getElementById("wrong").getBBox(), st = document.getElementById("strike");
  st.setAttribute("x", bb.x); st.setAttribute("width", bb.width); st.setAttribute("y", bb.y + bb.height * .55);

  gsap.set("#needle", { rotation: 10, svgOrigin: "0 0" });
  gsap.set("#strike", { scaleX: 0, transformOrigin: "left center" });
  gsap.set("#fix", { opacity: 0 });

  const tl = gsap.timeline({ paused: true });
  // 1 · gauge: free swing → clamp → forced back → strain
  tl.to("#needle", { rotation: 160, duration: .9, ease: "power2.out" })
    .from("#clamp", { y: -80, opacity: 0, duration: .35, ease: "back.out(2)" })
    .to("#needle", { rotation: 90, duration: .25, ease: "power3.in" }, "<.2")
    .to("#needle", { rotation: 94, duration: .06, yoyo: true, repeat: 9, ease: "none" })
  // 2 · hand-off a → b → c, receiver pulses
    .addLabel("pass", "+=.2");
  [["a","b"],["b","c"]].forEach(([f,t], i) => tl
    .to("#hat", { duration: .7, ease: "power1.inOut",
                  motionPath: { path: arcBetween(f,t), alignOrigin: [.5,1] } }, `pass+=${i*.9}`)
    .to("#"+t, { scale: 1.15, transformOrigin: "center", duration: .12, yoyo: true, repeat: 1 }, `pass+=${i*.9+.6}`));
  // 3 · correction
  tl.to("#strike", { scaleX: 1, duration: .3, ease: "power2.out" }, "+=.3")
    .to("#fix", { opacity: 1, duration: .3 }, "+=.15");

  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const t = new URLSearchParams(location.search).get("t");
  if (t !== null) tl.seek(parseFloat(t));
  else if (reduce) tl.progress(1);
  else tl.play();
  window.__ready = true;
  console.log("duration", tl.duration());
</script>
</body></html>
```

Frames to check: `t=0` needle at rest, no clamp · `t=0.9` needle in the red, clamp not yet down · `t=1.6` clamped, needle forced to centre · `t=2.5` hat mid-arc between the first two figures · `t=5.5` strike-through complete, "recycled" visible.

## 5. Magnifier lock-on (selection by one criterion)

```js
// magnifier slides across candidates; on the decisive one, it stops and the lens content scales up
tl.to("#lens", { x: 220, duration: .8, ease: "power1.inOut" })      // passes the person
  .to("#lens", { x: 460, duration: .6, ease: "power2.out" })        // arrives at the collateral stamp
  .to("#lens-content", { scale: 1.6, transformOrigin: "center", duration: .25 }, "<.45")
  .to(".ignored", { opacity: .3, duration: .3 }, "<");             // the criteria it ignored grey out
```

Use a `<clipPath>` circle for the lens and render a scaled copy of the document inside it so the zoom is a true magnification, not a separate image.

---
Animate the verb, label what's simplified, and let a few props come back stronger. Built by **[iart.ai](https://iart.ai/?utm_source=github&utm_medium=readme&utm_campaign=explainer-video-skills&utm_content=skill_footer&utm_term=visual-metaphor)** — the AI motion agent for editable, on-brand motion graphics.
