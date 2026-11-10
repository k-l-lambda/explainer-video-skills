---
name: create-image
description: Generate or edit images with the gpt-image-2 endpoint via the bundled scripts/genimage.py. Use when asked to produce, generate, edit or regenerate artwork, covers, sprites, illustrations, explainer stills or any raster image asset.
---

# Generating images

One endpoint is available: `POST $CLAUDE_BASE_URL/v3/gpt-image-2-text-to-image`,
authenticated with `Authorization: Bearer $PAIGOD_API_KEY`. Both come from the
environment; never hardcode the host or the key. These paths are that gateway's own;
another provider needs its paths in the script.

`${CLAUDE_SKILL_DIR}` is this skill's folder; in an agent that does not substitute it, use the folder this `SKILL.md` is in. The wrapper is Python 3 with the standard library only.

Call it through the wrapper rather than by hand:

```bash
${CLAUDE_SKILL_DIR}/scripts/genimage.py PROMPT_FILE OUT.png [--quality low|medium|high] [--size WxH] [--n 1-10]
```

The prompt goes in a **file**, not on the command line. Prompts for real artwork
run to several hundred words and carry exact hex values, quotes and backticks; a
shell mangles those, and a mangled prompt still returns a perfectly nice picture
of the wrong thing, so the damage is silent.

```bash
${CLAUDE_SKILL_DIR}/scripts/genimage.py prompts/cover.txt out/cover.png --quality high
${CLAUDE_SKILL_DIR}/scripts/genimage.py brief.txt draft.png --quality low --n 4   # draft-1..4.png
echo "a red ball" | ${CLAUDE_SKILL_DIR}/scripts/genimage.py - ball.png --quality low
```

## Parameters

| Parameter | Values | Notes |
|---|---|---|
| `prompt` | up to 32000 chars, Chinese or English | required |
| `size` | `1024x1024`, `1024x1536`, `1536x1024`, `2048x2048`, `2048x1152`, `3840x2160`, `2160x3840`, `2048x1360`, `1360x2048`, `1152x2048`, `2048x1536`, `1536x2048`, `2048x880`, `880x2048`, `688x2048`, `2048x688`, `2048x1024`, `1024x2048`, `auto` | default `1024x1024` |
| `quality` | `low`, `medium`, `high` | default `medium`; the tool defaults to `high` |
| `output_format` | `png`, `jpeg` | default `png` |
| `background` | `opaque`, `auto` | **no transparency exists**, see below |
| `n` | 1–10 | one call, several variants; may return fewer |
| `moderation` | `low`, `auto` | default `auto` |
| `output_compression` | 0–100 | jpeg only; png must be 100 or unset |
| `image` | base64, `data:` URI or URL; string or array | **`-edit` only, required there** |
| `mask` | PNG with an alpha channel | `-edit` only; transparent areas are what may change |

A 400 lists the valid values for whichever parameter is wrong, so the table above
can be re-derived from the server at any time rather than trusted blindly.

Measured timings at `1024x1024`: `low` ~18–22s, `medium` ~35–50s, `high` ~2m20s.
`n` does not scale the wait linearly — three `low` images came back in 22s, about
the same as one — so asking for several variants at once is close to free.

`high` exceeds a 120s foreground command timeout. Run it in the background and
wait on the output file appearing rather than blocking on the call.

## Editing an existing image

A second endpoint, `POST $CLAUDE_BASE_URL/v3/gpt-image-2-edit`, edits an image
instead of generating one from nothing:

```bash
${CLAUDE_SKILL_DIR}/scripts/genimage.py PROMPT_FILE OUT.png --edit SOURCE.png [--mask MASK.png]
${CLAUDE_SKILL_DIR}/scripts/genimage.py PROMPT_FILE OUT.png --edit a.png --edit b.png   # several references
```

Same response shape as text-to-image. Its parameters differ in three ways worth
knowing: `image` is **required**, `quality` defaults to **`low`** rather than
`medium`, and a `mask` is accepted — a PNG whose **fully transparent areas mark
where editing is allowed**, which is inpainting. `image` takes a bare base64
string, a `data:` URI, or an http(s) URL, and either a single string or an array
for multiple references; PNG, JPEG, GIF and WebP are supported. The wrapper
base64-encodes a local path and passes a URL through untouched.

**It genuinely preserves the source.** Asked to warm the sky of a finished cover,
it moved the sky from `#e2f2f5` to `#faefda` while **0.0% of pixels changed by
more than 30**, and the three fish came back within 0.5% of their original areas.
A second edit changing only flowers altered 2.26% of pixels and left the fish
count and the cat's coverage intact. So this is the tool for keeping a character
consistent across images — generate one figure, then edit it into new situations
rather than re-rolling the prompt and hoping.

It does **not** solve video start frames; that is a property of the video API,
not this one.

## What this endpoint cannot do

- **No transparent background.** `background` accepts only `opaque` and `auto`;
  neither yields an alpha channel. Output is RGB. Anything needing cut-out layers
  must be composited another way.
- Only these two contracts are live under `/v3/` for images: `-text-to-image` and
  `-edit`. Other names return `unsupported native endpoint contract` — but note
  that error also appears for a *valid* path given a body it cannot match, so it
  is not by itself proof that an endpoint is absent. Guessing `-image-to-image`
  and reading its failure as "no such capability" is exactly the wrong inference
  to draw; the capability existed under a different name.

## Two traps that cost real time

**The success signal is `images`, not `base_resp`.** Two response shapes come
back. One carries `base_resp: {status_code: 0, status_msg: "success"}` and
nothing else; the other omits `base_resp` entirely and echoes the parameters it
used. Code that keys success on `base_resp.status_code == 0` reports a perfectly
good image as a failure. The wrapper already handles this.

**The response is a signed URL, not image bytes.** It is time-limited, so it
must be downloaded immediately; there is no point recording it for later. The
wrapper does the download as a second step.

A 400 is worth reading rather than guessing past: validation errors quote the
entire request schema back, including enums and defaults. `-d '{}'` is the
cheapest way to get authoritative parameter documentation.

## Getting the colours you asked for

Named hex values **drift, and emphasis moves them without pinning them**. Treat
the hex as a strong hint, never as a guarantee.

Asking for a fish body at `#5cc3e8` first returned `#7cc4e4` — right hue, washed
out. Re-prompting the same value with emphasis landed it exactly, at `high`:

- write the value as `exactly #5cc3e8`
- add the negative form: `fully saturated, not pale, not washed out, not white-tinted`
- say why, in one clause: `must match sprite characters that already use these precise colours`

But the same emphasis **overshoots** as readily as plain wording undershoots. A
banana briefed at `#f7d84a` with that exact phrasing came back `#fcd424` at
`low`: red and green almost exact, blue 38 off, pushed past the target because
"fully saturated, not pale" is a direction rather than a stopping point. A second
colour in the same prompt (`#e0b92c`) landed within 2 per channel at the same
time, so accuracy varies *within* one image, not just between renders.

What follows for colour-critical work:

- measure every briefed colour separately; one being exact says nothing about the next
- generate several variants at `low` and compare before paying for a `high` render
  — variants from a single `--n` call differed by 1 vs 9 per channel on the same value
- expect to iterate on wording, and accept a near miss in the right hue family
  rather than chasing an exact match that the endpoint may not hit

## Verify what came back by measuring it

Some sessions cannot view an image at all (in the project these notes come from,
`Read` on an image returned `.`), and where one can, a look does not give a hex
value or a count. So every claim about the result is measured, with PIL and numpy
(scipy for labelling). Without OCR and without a look at the image, text in it
cannot be detected: never claim an image is free of text or that a character
resembles a reference; report those as needing human eyes.

Worth measuring, and enough to catch real failures:

- **size and mode** — `Image.open(p).size`, `.mode`
- **flat-vector style** — count colour buckets with `(px // 16)`; flat art lands
  in the hundreds, a photo or glossy render in the thousands
- **palette presence** — fraction of pixels within ~30 per channel of each
  briefed hex
- **figure count** — `scipy.ndimage.label` on a colour-family mask, after
  `binary_closing` to rejoin a figure split by its own outline. Filter blobs by
  fill ratio (area ÷ bounding box): a drawn figure fills roughly two thirds, a
  painted line or edge a few percent. This is the check that catches art
  contradicting its purpose, such as a counting cover showing the wrong number
  of objects.
- **crop safety** — if the image will be cropped to a circle, locate the figure
  as a blob and confirm it sits inside the inscribed circle. Do not test for
  uniform corners; a full scene is supposed to have scenery there.

**Prove a check fires before trusting its silence.** Build a deliberately wrong
image and confirm the check fails on it. Checks written against these covers were
wrong three times in ways that only a control exposed: one tested for quiet
corners the brief never asked for; one used a pale marker colour that matched 85%
of the sky, so it measured background instead of subject; and a repaired version
went silent because it examined only the largest blob. A check that passes
everything looks exactly like a clean result.

When measuring a figure's colour, sample only the mask pixels. Averaging a
bounding box mixes in outline and background and reports a shade that appears
nowhere in the image.
