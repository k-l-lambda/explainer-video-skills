---
name: create-video
description: Generate video clips with the Dreamina Seedance endpoint via the bundled scripts/genvideo.py. Use when asked to produce, generate or regenerate video, animation, motion, a clip or generated b-roll for an explainer.
---

# Generating video

Asynchronous, in two calls:

```
POST $CLAUDE_BASE_URL/v3/bytedance/metered/contents/generations/tasks      -> {"id": "cgt-..."}
GET  $CLAUDE_BASE_URL/v3/bytedance/metered/contents/generations/tasks/ID   -> {"status": ...}
```

Authenticated with `Authorization: Bearer $PAIGOD_API_KEY`. Both host and key
come from the environment; never hardcode either. These paths are that gateway's
own; another provider needs its paths in the script.

`${CLAUDE_SKILL_DIR}` is this skill's folder; in an agent that does not substitute it, use the folder this `SKILL.md` is in. The wrapper is Python 3 with the standard library only.

Use the wrapper, which creates and then polls:

```bash
${CLAUDE_SKILL_DIR}/scripts/genvideo.py PROMPT_FILE OUT.mp4 [--duration 5] [--ratio 1:1] [--resolution 720p]
${CLAUDE_SKILL_DIR}/scripts/genvideo.py --task cgt-<task id> OUT.mp4   # resume or refetch
```

## A task cannot be undone

**There is no cancel.** `DELETE` on a task and `POST .../{id}/cancel` both return
`unsupported native endpoint contract`. Create and poll are the entire surface,
so every created task runs to completion and bills.

**Values are validated by starting work, not before it.** An invalid `--ratio`
is refused for free, but a valid one begins a real generation. Sweeping an enum
to discover what it accepts therefore costs one video per value — this was
learned by doing it, and it created eleven unwanted clips that could not be
stopped. The accepted values are recorded below so nobody needs to repeat that.
`${CLAUDE_SKILL_DIR}/scripts/genvideo.py` checks them locally before it calls out.

Generation takes **several minutes**, far longer than an image. Poll on an
interval; do not block a foreground command on it.

## Model and parameters

Only `dreamina-seedance-2-5-260628` works. `seedance-2.0` appears in
`GET /v1/models` but returns `InvalidEndpointOrModel.NotFound`. Requests resolve
internally to `eva-video-2.5-t2v-480p-720p`, which is text-to-video only.

Parameters arrive **two different ways**, which is the easiest thing to get wrong:

| Parameter | Where it goes | Values |
|---|---|---|
| prompt | `content: [{type: 'text', text: ...}]` | required; a bare `prompt` field is rejected |
| first frame | a second `content` part, `{type: 'image_url', image_url: {url}}` | a data URL or an http(s) URL |
| `--ratio` | appended to the prompt text | `1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `21:9`, `adaptive` |
| `--resolution` | appended to the prompt text | `480p`, `720p`, `1080p` (`2k` and `4k` rejected) |
| `duration` | top-level JSON field | `-1`, or `4`–`30` seconds |
| `generate_audio` | top-level JSON field | **defaults to `true`** |

`content` must be a list of typed parts. Sending `{"prompt": "..."}` fails with
`expr_path=content, cause=missing required parameter`. The accepted part types are
`text`, `image_url`, `audio_url`, `video_url` and `draft_task` — the service lists
them when given an invalid one, which is a free way to read that enum.

**A first frame is supported**, despite the model resolving to a name ending
`t2v`. Pass the image as a second `content` part; `${CLAUDE_SKILL_DIR}/scripts/genvideo.py --first-frame`
does it, reading a local file and inlining it as a base64 data URL so nothing is
uploaded anywhere. Two things change when you do:

- **`--ratio` must be dropped.** The output ratio follows the first frame, and
  sending a ratio as well is rejected with `InvalidParameter.TaskTypeConstraint`.
  `--resolution` is still required.
- The first frame is reproduced closely but not exactly: re-encoding puts it about
  3-4 per channel from the source image. A clip generated *without* a first frame
  measures 54-63 against its intended opening still, so the two cases are far
  apart and easy to tell apart in a check.

**`duration: -1` is not a free probe.** It is documented as valid and behaves as
valid: it starts a real billed generation. An out-of-range value cannot be used to
test the rest of a body — use a deliberately corrupt `image_url` instead, which is
refused at decode for nothing.

**`generate_audio` defaults on.** For a silent project this is wrong by default
and has to be turned off explicitly; `${CLAUDE_SKILL_DIR}/scripts/genvideo.py` defaults it off and
takes `--audio` to enable it. A clip generated without the flag came back
carrying a real AAC stereo track at 32 kHz, so this is not a nominal setting.

**Measured defaults**, from a request that specified neither ratio nor duration:
`1280x720` (16:9), 5.04s, 24fps, h264 in MP4, about 2.2 MB. So the default aspect
is landscape — a square clip needs `--ratio 1:1` explicitly.

The finished video arrives at **`content.video_url`** in the task payload, as a
time-signed TOS link (`X-Tos-Expires=86400`). It has to be downloaded; there is
no inline data.

An empty `{}` body returns `unsupported native endpoint contract`, which looks
exactly like a wrong URL and sent an earlier attempt hunting for a path that was
correct all along. The contract is matched against the **body**, so probe with a
minimally valid body, not an empty one.

## Writing the prompt

Give a **shot list with second ranges**, not a description. A brief without
timing comes back as one continuous drift with no beats:

```
0.0 to 1.5 seconds: <beat>
1.5 to 3.0 seconds: <turn>
3.0 to 4.5 seconds: <landing>
4.5 to 5.0 seconds: hold on <final pose>
```

State `camera completely still, no pans and no zooms` if the frame should not
move; generators drift toward camera motion otherwise. Restate any invariant as
an absolute — `exactly three fish visible in every frame from start to finish,
none enters, leaves or hides` — because a count that changes mid-clip is a
failure a viewer notices and a thumbnail does not show.

Colour behaves as it does for images: see the `create-image` skill. Hex values
drift, emphasis moves them without pinning them, and accuracy varies within a
single render.

## Verify the clip by measuring it

Measure the clip with `ffprobe`, `ffmpeg`, `cv2` and `av`. Even where frames can
be viewed, a look does not give counts, colours or the frame where something changed.

Cheap and worth doing every time:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams OUT.mp4
```

That gives duration, dimensions, codec, fps, frame count, and whether an audio
stream exists — the last one catches `generate_audio` being left on.

Then check the content **per frame**. Decode with `cv2.VideoCapture`, sample
every Nth frame, and measure the colour family described in `create-image` on
each one. Scale any area floor to the frame size; these clips come back smaller
than a 1024px cover.

**Measure total area of the colour family, not the number of blobs.** Blob count
is what a still image wants, and it is wrong for video: two figures that touch or
overlap merge into one connected component, so the count collapses while nothing
has actually left the frame. On a real clip this produced a dramatic false alarm
— 14 of 25 sampled frames appeared to break a "exactly three fish" rule. Two
things were actually happening, neither a defect:

- the splash the brief asked for threw **droplets in the same colour family**,
  counted as extra figures. Sizes separated the populations cleanly: fish
  ~5000–5500px, droplets 620–1828px, no overlap between the groups.
- during the splash the fish **touched and merged**, so the count read 1 while
  the total blue area was still 1.06–1.24x its pre-splash baseline.

Total area over a size floor stayed within 0.80–1.51x baseline for the whole
clip, which is the honest statement that nothing vanished. So: use area as the
invariant, use a size floor to exclude effects like droplets, and treat a
count anomaly as **a frame range to look at**, never as a verdict. Occlusion and
absence are not distinguishable by these means, and claiming otherwise is how a
good clip gets thrown away.

**A zero reading is usually a wrong mask, not a missing subject.** Two ways this
happened on the same project, and both looked like a defect in the clip:

- **The family colour drifted.** Measuring `l1-clear.mp4` for the fish blue
  `#5cc3e8` returned *zero pixels over the size floor in every frame*, which reads
  as "the fish are gone". The fish were there the whole time; the generator had
  rendered them paler than the brief, closest actual pixel 33.7 away, while the
  pool water matched its own hex to 5.7. Segmenting by hue band plus a saturation
  floor instead found them immediately: 2-3 blobs of about 1500px, present from
  frame zero. So before believing a zero, check that the target colour is present
  in the frame at all — and if the subject and its background share a hue,
  saturation is what separates them, not distance to a hex.
- **The tolerance reached the background.** A mask needs a tolerance below half the
  distance to the nearest colour it could be confused with. The rabbit's `#f3f0ea`
  is 16.3 from the sky's `#eaf4f7`, so at a tolerance of 44 the "rabbit white"
  mask was a sky mask, and the sky warming to amber at the end of the clip read as
  the rabbit vanishing. Compute the tolerance from the palette rather than picking
  one, and report a family too close to its background as unmeasurable instead of
  asserting it.

**Build a control before trusting a clean result.** A synthetic clip holding
three figures for half its length and four for the rest confirmed the per-frame
check reports the frame where a count changes. A checker that reads frame 0 and
never looks again is indistinguishable from a correct clip.

What these measurements cannot check: whether text appears, and whether characters
resemble a reference. Without OCR and without a look at the frames, report both as
needing human eyes rather than asserting them.
