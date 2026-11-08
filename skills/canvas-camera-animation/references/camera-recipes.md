# Camera Recipes — Cookbook

A deterministic camera over a 2D board: keyframed stations, log-space zoom, parallax, focus pull, velocity blur and whips. One clock drives everything, so `?t=N` lands on an exact frame.

## 1. Camera as a pure function of time

Don't tween the camera with stateful tweens if you need velocity (for blur). Write the camera as `camAt(t)` over keyframes. Velocity is then `camAt(t) - camAt(t - dt)`, which still works when you seek.

```js
// t: seconds · x,y: world point at viewport centre · z: zoom · f: focus layer (parallax factor)
const K = [
  { t: 0,    x: 0,    y: 0,   z: 1,   f: 1 },
  { t: 1.0,  x: 0,    y: 0,   z: 1,   f: 1 },
  { t: 2.2,  x: 1400, y: 0,   z: 1,   f: 1 },
];
const ease = u => u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u + 2, 3) / 2;   // easeInOutCubic
const lerp = (a, b, u) => a + (b - a) * u;
function camAt(t) {
  if (t <= K[0].t) return { ...K[0] };
  for (let i = 0; i < K.length - 1; i++) {
    const a = K[i], b = K[i + 1];
    if (t <= b.t) {
      const e = ease((t - a.t) / (b.t - a.t));
      return { x: lerp(a.x, b.x, e), y: lerp(a.y, b.y, e),
               z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), e)),   // log-space zoom
               f: lerp(a.f, b.f, e) };
    }
  }
  return { ...K[K.length - 1] };
}
```

A **hold** is two keyframes with the same values. A **hop** to a far station is out (lower z) → travel → in. A **whip** is a travel segment of 0.25–0.4s; the blur below kicks in automatically because it's fast.

## 2. Runnable board — stations, parallax, focus pull, whip blur

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>Canvas camera</title>
<style>
  html,body{margin:0;height:100%;overflow:hidden;background:#2f5d50}
  #cam{position:absolute;inset:0;overflow:hidden}
  .layer{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform,filter}
  .grid{width:9000px;height:5000px;left:-2500px;top:-2500px;
    background-image:linear-gradient(rgba(255,255,255,.13) 1px,transparent 1px),
                     linear-gradient(90deg,rgba(255,255,255,.13) 1px,transparent 1px);
    background-size:48px 48px}
  .card{position:absolute;background:#efe9dc;color:#1d1d1b;padding:28px 36px;
    box-shadow:4px 6px 10px rgba(0,0,0,.3);font:700 46px/1.1 Georgia,serif}
  .small{font:400 20px/1.5 "Courier New",monospace;margin-top:14px}
  .tag{font:italic 14px Georgia,serif;color:#6b665c}
  .hl{background:linear-gradient(#21b8c6,#21b8c6) no-repeat 0 88%/var(--hl,0%) 42%}
  .thread{position:absolute;height:3px;background:#21b8c6;transform-origin:0 50%}
  .scrap{position:absolute;width:260px;height:150px;background:#e4dccb;opacity:.9;
    box-shadow:6px 10px 14px rgba(0,0,0,.35)}
</style></head>
<body>
<div id="cam">
  <div class="layer grid" data-p="0.6"></div>
  <div class="layer" data-p="1">
    <div class="card" id="s1" style="left:-320px;top:-90px;width:640px">Where does the money go?</div>
    <div class="thread" id="th1" style="left:360px;top:0;width:700px"></div>
    <div class="card" id="s2" style="left:1100px;top:-150px;width:600px">Record savings
      <div class="small">deposits ÷ GDP <span id="key" class="hl">≈ 1.2×</span></div>
      <div class="tag">illustrative figure</div></div>
    <div class="card" id="s3" style="left:2600px;top:-90px;width:640px;min-height:110px"><span id="typed"></span></div>
  </div>
  <div class="layer" data-p="1.5">
    <div class="scrap" style="left:700px;top:260px;transform:rotate(-4deg)"></div>
    <div class="scrap" style="left:2050px;top:-420px;transform:rotate(3deg)"></div>
  </div>
</div>
<svg width="0" height="0" style="position:absolute">
  <filter id="mb" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="mbk" stdDeviation="0 0"/></filter>
</svg>
<script>
// Stations are anchored to elements ("at"), not hand-typed coordinates: text metrics vary by font,
// and a push-in aimed at a guessed point lands on empty paper.
const K = [
  { t: 0,    at: "#s1",  z: 1 },
  { t: 1.0,  at: "#s1",  z: 1 },              // S1 hold
  { t: 2.2,  at: "#s2",  z: 1 },              // pan → S2 (follows the thread)
  { t: 2.7,  at: "#s2",  z: 1 },
  { t: 3.7,  at: "#key", z: 3.2 },            // push-in on the figure
  { t: 5.2,  at: "#key", z: 3.2 },            // hold while it highlights
  { t: 6.0,  at: "#s2",  z: .85, f: 1.5 },    // hop out, focus pulls to foreground
  { t: 6.35, at: "#s3",  z: .85, f: 1.5 },    // whip → S3
  { t: 7.1,  at: "#s3",  z: 1 },              // settle, focus back
  { t: 9.0,  at: "#s3",  z: 1 },
];
// resolve anchors in world px: measured before any layer transform is applied (world = viewport here)
for (const k of K) {
  const r = document.querySelector(k.at).getBoundingClientRect();
  k.x = r.left + r.width / 2 + (k.dx || 0); k.y = r.top + r.height / 2 + (k.dy || 0); k.f = k.f ?? 1;
}
const DUR = K[K.length - 1].t;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const ease = u => u < .5 ? 4*u*u*u : 1 - Math.pow(-2*u + 2, 3) / 2;
const lerp = (a, b, u) => a + (b - a) * u;
const clamp01 = u => Math.max(0, Math.min(1, u));
function camAt(t) {
  if (t <= K[0].t) return { ...K[0] };
  for (let i = 0; i < K.length - 1; i++) {
    const a = K[i], b = K[i + 1];
    if (t <= b.t) {
      let e = ease((t - a.t) / (b.t - a.t));
      if (reduce) e = t < b.t ? 0 : 1;               // reduced motion: cut instead of move
      return { x: lerp(a.x, b.x, e), y: lerp(a.y, b.y, e),
               z: Math.exp(lerp(Math.log(a.z), Math.log(b.z), e)), f: lerp(a.f, b.f, e) };
    }
  }
  return { ...K[K.length - 1] };
}
const layers = [...document.querySelectorAll(".layer")].map(el => ({ el, p: +el.dataset.p }));
const camEl = document.getElementById("cam"), mbk = document.getElementById("mbk");
const typedText = "Who decides where it goes?";

function render(t) {
  const vw = innerWidth, vh = innerHeight, c = camAt(t), b = camAt(t - 1/60);
  for (const { el, p } of layers) {
    el.style.transform = `translate(${vw/2}px,${vh/2}px) scale(${c.z}) translate(${-c.x*p}px,${-c.y*p}px)`;
    const dof = Math.min(8, 6 * Math.abs(p - c.f));            // fake depth of field
    el.style.filter = dof > .05 ? `blur(${dof.toFixed(2)}px)` : "none";
  }
  // velocity blur in screen px/s; slow pans stay sharp (threshold), whips smear
  const vx = Math.abs(c.x - b.x) * c.z * 60, vy = Math.abs(c.y - b.y) * c.z * 60;
  const sx = reduce ? 0 : Math.min(28, Math.max(0, (vx - 5000) / 150));
  const sy = reduce ? 0 : Math.min(28, Math.max(0, (vy - 5000) / 150));
  mbk.setAttribute("stdDeviation", `${sx.toFixed(1)} ${sy.toFixed(1)}`);
  camEl.style.filter = sx + sy > .1 ? "url(#mb)" : "none";
  // content driven by the same clock
  document.getElementById("th1").style.transform = `scaleX(${clamp01((t - 1.0) / 1.2)})`;
  document.getElementById("key").style.setProperty("--hl", `${100 * clamp01((t - 3.9) / .5)}%`);
  document.getElementById("typed").textContent = typedText.slice(0, Math.floor(clamp01((t - 7.0) / 1.2) * typedText.length));
}

const q = new URLSearchParams(location.search).get("t");
if (q !== null) render(parseFloat(q));
else { const t0 = performance.now();
  (function loop(now) { const t = Math.min(DUR, (now - t0) / 1000); render(t); if (t < DUR) requestAnimationFrame(loop); })(t0); }
addEventListener("resize", () => q !== null && render(parseFloat(q)));
window.__ready = true;
console.log("duration", DUR);
</script>
</body></html>
```

Frames to check: `t=0.5` S1 centred · `t=1.6` mid-pan, sharp (slow move), thread half drawn · `t=4.6` pushed in at 3.2×, figure highlighted and crisp · `t=6.15` mid-whip, strong horizontal blur, foreground in focus · `t=8.5` S3 centred, question typed.

Notes:
- Station layer is `p = 1`, so resolved `x, y` are exact world coordinates of the anchored element. Use `dx/dy` to offset framing.
- Parallax here shares the zoom across layers. For deeper scenes, also scale layers by `z ** p` so the foreground grows faster on push-ins.
- The blur threshold (5000 px/s on screen) is the knob. `easeInOutCubic` peaks at 3× the average speed, so a 1400px pan over 1.2s peaks near 3500 px/s and stays sharp, while a 0.35s whip peaks above 10000 px/s and smears. Lower the threshold for a looser hand-held feel.

## 3. Remotion port

```tsx
import { AbsoluteFill, interpolate, Easing, useCurrentFrame, useVideoConfig } from "remotion";
import { CameraMotionBlur } from "@remotion/motion-blur";

const K = [ { t: 0, x: 0, y: 0, z: 1 }, { t: 1, x: 0, y: 0, z: 1 }, { t: 2.2, x: 1400, y: 0, z: 1 } /* … */ ];
const opt = { easing: Easing.inOut(Easing.cubic), extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Board: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps, ts = K.map(k => k.t);
  const x = interpolate(t, ts, K.map(k => k.x), opt);          // easing applies per segment
  const y = interpolate(t, ts, K.map(k => k.y), opt);
  const z = Math.exp(interpolate(t, ts, K.map(k => Math.log(k.z)), opt));
  return (
    <CameraMotionBlur shutterAngle={180} samples={8}>
      <AbsoluteFill style={{ background: "#2f5d50" }}>
        <div style={{ position: "absolute", transformOrigin: "0 0",
          transform: `translate(${width/2}px,${height/2}px) scale(${z}) translate(${-x}px,${-y}px)` }}>
          {/* stations in world px */}
        </div>
      </AbsoluteFill>
    </CameraMotionBlur>
  );
};
```

`<CameraMotionBlur>` renders `samples` sub-frames per frame, so render time multiplies. Wrap only the `<Sequence>`s that contain whips, or use the threshold blur from section 2 instead.

## 4. Whip-pan recipe

- Out → travel → in: drop zoom 10–20% for the whip, restore on landing.
- Travel 0.25–0.4s, `easeInOutCubic`; the blur peaks mid-travel.
- Land with a tiny settle: overshoot 1–2% of the distance and ease back over 0.2s.
- Sound: a short whoosh peaking at mid-travel; land the next VO line within 0.3s.
- Use it only for a jump in time or case *within the same world*. To leave the world (to footage, to a dramatized scene) use a cut or a white flash.

## 5. Following a path (flow follow)

```js
// path: <path id="route"> in world coords; a token rides it, the camera trails slightly
const route = document.getElementById("route"), L = route.getTotalLength();
function followAt(t, t0, dur) {
  const u = clamp01((t - t0) / dur);
  const tok = route.getPointAtLength(L * ease(u));
  const cam = route.getPointAtLength(L * ease(Math.max(0, u - .04)));  // 4% lag = "following"
  return { token: tok, cam: { x: cam.x, y: cam.y } };
}
```

Merge the follow segment into `camAt` by returning `followAt(...).cam` while `t` is in that window.

## 6. Ken Burns on a document

For a single scanned document, use the same rig with one station: start at `z = 1` on the whole page, push to the decisive line (`z = 3–5`), hold through the VO quote, then pull out. Author the highlight as a DOM/SVG overlay positioned in page coordinates so it stays aligned at every zoom.

---
One clock, one camera, stations in reading order: the board explains itself as the camera travels. Built by **[iart.ai](https://iart.ai/?utm_source=github&utm_medium=readme&utm_campaign=explainer-video-skills&utm_content=skill_footer&utm_term=canvas-camera-animation)** — the AI motion agent for editable, on-brand motion graphics.
