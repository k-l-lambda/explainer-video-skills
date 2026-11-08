---
name: longform-explainer
description: This skill should be used when the user asks to "make a long-form explainer", "plan a 10–40 minute video essay", "structure a chaptered documentary explainer", "write a cold open", "design a title sequence for an explainer series", "keep viewers watching a long video", "chain chapters so each one hooks the next", or "turn research into a narrated deep-dive". Covers argument architecture, cold open + title, chapter bridges, steelman counterexamples, callbacks, evidence discipline, and pacing over long runtimes.
version: 0.1.0
---

# Long-form Explainer (10–40 min)

A long explainer is an investigation the viewer follows, not a short explainer stretched. The 30–90s formula in **explainer-video** (problem → solution → how → payoff) still holds inside each chapter, but a 30-minute piece needs more: a question big enough to carry the whole runtime, chapters that hand the viewer from one question to the next, an honest counter-argument, and a payoff that re-reads the opening.

## When to use

- Narrated video essays, documentary explainers, "deep dive" episodes, lecture-style series.
- Any explainer over ~5 minutes, or one split into chapters.
- Planning a cold open, title card or series intro for an explainer channel.
- Diagnosing why a long draft loses viewers in the middle.

For scenes inside a chapter, pair with **visual-metaphor** (what to show), **canvas-camera-animation** (how to move through it) and **diagram-animation** (charts and flows). To learn from an existing film, start with **reference-video-analysis**.

## Core principle: one question, many handoffs

Pick **one central question** the viewer cannot answer yet, and make every chapter either sharpen it, answer part of it, or raise the next sub-question. Retention past minute three comes from open questions, not from cut speed.

### Start from a tension pair

Write the topic as two observations that are both true and seem to contradict each other: *"Savings are at a record high"* + *"Small firms can't borrow."* The central question falls out of the gap ("So where does the money go?"). A tension pair beats a definition because the viewer already has a stake in resolving it.

Test: can a viewer repeat the question after the first 60 seconds? If not, the opening is a topic, not a hook.

## Architecture at a glance

| Part | Share | Job |
|---|---|---|
| Cold open | 2–4% | Tension pair → reversal → one insider line → title |
| Setup | 5–10% | Who/what we follow; why now; promise of what the video will answer |
| Foundations | 10–15% | The one mental model needed, built from an everyday case |
| Investigation | 35–45% | Mechanism chapters, each answering a sub-question and raising the next |
| Steelman | 5–10% | The strongest counter-example, answered on its own terms |
| System → people | 10–15% | Zoom from the system to the individual choices that produce it |
| Resolution | 8–12% | Callback: re-read the opening line and question with the new model |
| Outro / next | 2–4% | Shift the frame one notch and hand off to the next episode |

Full beat sheet, chapter-card template and a worked 35-minute breakdown: `references/chapter-architecture.md`.

## Cold open and title

The cold open runs **before** any title or host intro. A dependable beat order:

1. **Ask** the question in the viewer's words.
2. **Let them answer**, with the everyday answer ("Of course we're short of money: rent, salary…").
3. **Reverse** it with one hard number or fact.
4. **Escalate** with one insider line or scene that deepens the mystery.
5. **Title card** that states the question or a provocative claim. The host/mascot appears only now.

Cut rhythm is fastest here (a measured case: ASL ≈ 4s in the first chapter vs 10s for the film, with whip-pan bursts on top). A "TV-series" title sequence is optional: if you add one, keep it 5–15s, built from the film's own motifs (props, material, type) so the ending can reuse it. It should preview the conflict, never the answer. Don't borrow a show's logo, music or sequence.

## Chapter bridges

Each chapter ends by handing the viewer a reason to watch the next. Measured in one 35-minute essay: 38 question lines (about one a minute). Of its 18 chapters, 3 close on a literal question; the rest hand off with an objection, a named next concept or the refrain. Mix the bridge types; don't end every chapter on "?".

| Bridge | Shape | Example |
|---|---|---|
| Question handoff | End on the question the next chapter answers | "What does a credit system that can compute look like? Let's look at…" |
| Objection handoff | Voice the viewer's objection | "Someone will say: what about 2008?" → next chapter: "Good question." |
| Zoom handoff | System → person, or person → system | "…and that lands on every individual." → five persona cards |
| Callback handoff | Return to a planted line | "Now we can explain what that banker meant." |
| Refrain | Close on the thesis phrase | "…so prices stop telling the truth." |

Keep chapter titles as questions or claims, not topic labels ("Is scan-to-pay ahead if credit isn't?" beats "Payments"). They double as the YouTube chapter list.

## Devices that carry a long runtime

- **Refrain.** One short phrase that compresses the thesis ("prices stop telling the truth"), said at 3–5 chapter ends and given a visual form (a recurring prop). It ties chapters together without a recap.
- **Named everyman.** One concrete person stands in for "the borrower" so mechanisms happen *to someone*. Reuse the same person across chapters.
- **Ensemble chapter.** Show 3–5 actors each making the rational choice, then add them up to the irrational outcome. Useful for any emergent-effect argument.
- **Two-line ledger.** Replace an abstract flow with a small calculation the viewer can recompute (borrow at X, deposit at Y, the spread is the story). Label it "simplified".
- **Steelman chapter.** Pick the counter-example that genuinely threatens the thesis and answer it on its terms. A straw man costs trust for the rest of the film.
- **Plant → payoff.** Plant the opening quote/number; pay it off at ~85% of the runtime with "Now we can answer…". Track plants in a table so none are orphaned.
- **Frame shift at the end.** Change one word of the thesis to open the next episode (in the measured case, "who to *lend* to" became "who to *invest* in" with a one-character paper patch).

## Evidence discipline

Long explainers make many claims. Keep them separable on screen and in the script:

- Tag every script line as **fact / quote / estimate / opinion / illustration**, with a source column. Opinion lines are fine; unlabeled opinion dressed as fact is not.
- Numbers on screen carry **unit, date and source**. Simplified calculations say so.
- Use **media tiers** and never mix their roles. Archival footage and document scans are evidence. Diagrams and props show the mechanism. Stylized character scenes are for story. A dramatized scene must not look like footage. Anonymize reconstructed private conversations (faceless or masked figures).
- Grade archival footage toward the film's palette so it sits in the world, but keep it visibly *footage* (grain, frame, caption) so it stays distinguishable from illustration.

## Pacing over a long runtime

| Measure | Typical target | Why |
|---|---|---|
| Narration coverage | 75–90% of runtime | Long essays are VO-led; pauses are punctuation |
| Speech rate | EN ~150–170 wpm · ZH ~4.5–5.5 chars/s | Faster than short-form explainer pace; keep technical lines slower |
| Cut rhythm | Varies by chapter function | Hooks: bursts; cases: 3–8s; mechanisms: long continuous camera moves |
| Silence | A handful of 0.6–2s gaps | Spend them before a turn, a reveal or the outro |
| Loudness | −14 to −16 LUFS integrated, LRA ≤ 6 LU | Consistent VO level for long listening |

Vary density by chapter: a mechanism chapter can have **zero hard cuts** for a minute if the camera keeps moving through one continuous canvas (see **canvas-camera-animation**). Monotony comes from the same rhythm everywhere, not from long shots.

## Pipeline

1. **Research ledger**: claims, sources, numbers, quotes, status (verified/unverified).
2. **Tension pair + central question + thesis refrain.**
3. **Chapter cards**: inbound question, answer, outbound question, evidence, metaphor, bridge type.
4. **VO draft**, read aloud and timed per chapter; tag every line by evidence type.
5. **Metaphor cards** for each abstract relation (**visual-metaphor**).
6. **Canvas/camera board** per chapter: stations, camera path, cut points (**canvas-camera-animation**).
7. **Animatic** with scratch VO; check every chapter bridge plays.
8. **Build, mix, caption**, export chapters metadata.
9. **Review** on three independent tracks: visual, audio, facts.

## Output checklist

- Central question repeatable after 60s; cold open precedes title/host.
- Every chapter card has an inbound and outbound question; no chapter is skippable without losing the thread.
- Steelman chapter present and answered honestly.
- Every plant has a payoff; the opening line is re-read near the end.
- Refrain appears 3–5 times, verbally and visually.
- Every on-screen number has unit/date/source; illustrations labelled; dramatizations not styled as footage.
- Pacing varies by chapter function; silences are placed deliberately.
- Chapter titles are questions/claims and exported as timestamps.

## Deliver & verify

> **Packaged helpers** (`scripts/`): `sub-pacing.py` (speech rate, coverage, gaps, question lines per chapter), `shot-stats.py` (cuts and ASL per chapter), `audio-stats.sh` (LUFS, LRA, silences), `video-sheet.sh` (timestamped contact sheets). See `scripts/README.md`.

Build each chapter as its own Remotion composition (or NLE sequence) sharing one style system, then assemble; render stills at every chapter boundary and inside each chapter's longest hold.

```bash
python scripts/sub-pacing.py out/episode.vtt --chapters chapters.tsv   # rate, coverage, bridges
python scripts/shot-stats.py out/episode.mp4 --chapters chapters.tsv   # rhythm per chapter
scripts/audio-stats.sh out/episode.mp4                                 # LUFS / LRA / silences
scripts/video-sheet.sh out/episode.mp4 sheet-ch05.jpg 1260 2           # eyeball one chapter
scripts/probe-mp4.sh out/episode.mp4 1920x1080 30
```

**Before you finish:**
1. Pacing numbers sit in the target bands, or the deviation is intentional and noted.
2. Contact sheet of every chapter boundary shows the bridge (question card, callback, zoom) on screen.
3. Facts track reviewed: every number/quote matches the research ledger.
4. Captions and chapter timestamps exported and in sync with the final cut.

## Reference files

- `references/chapter-architecture.md` — beat sheet with runtime shares, chapter-card and plant/payoff templates, evidence ledger format, bridge library, and a worked breakdown of a measured 35-minute, 18-chapter essay (structure and numbers only).
