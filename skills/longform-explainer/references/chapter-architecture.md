# Chapter Architecture — Cookbook

Templates for planning a 10–40 minute explainer, plus a measured breakdown of a real 35-minute essay (structure and numbers only; the subject matter is irrelevant to the method).

## 1. Beat sheet (fill top to bottom)

```
CENTRAL QUESTION : one line, ends with "?"
TENSION PAIR     : A = "…"   B = "…"   (both true, seem contradictory)
THESIS REFRAIN   : ≤ 8 words, said 3–5 times
EVERYMAN         : name + one-line situation (reused across chapters)
STEELMAN         : the counter-example that most threatens the thesis
FRAME SHIFT      : the one-word change that opens the next episode
RUNTIME          : target minutes → word/char budget (EN 160 wpm · ZH 5 chars/s)
```

| Part | Share | Chapters | Typical content |
|---|---|---|---|
| Cold open | 2–4% | 1 | Ask → everyday answer → reversal number → insider line → title |
| Setup | 5–10% | 1 | Protagonist/case; why now; promise |
| Foundations | 10–15% | 1–2 | One mental model from an everyday example (a loan of rice, a queue) |
| Investigation | 35–45% | 4–7 | Comparison, named concept, mechanism, rules/power |
| Steelman | 5–10% | 1 | Strongest counter-case, answered on its own terms |
| Consequence | 5–10% | 1–2 | Who pays; the bill reaches the everyman |
| System → people | 8–12% | 1–2 | Ensemble of rational actors → irrational sum |
| Resolution | 8–12% | 1–2 | Callback to the opening line; answer the central question |
| Reflection / outro | 3–6% | 1–2 | Emotional beat, frame shift, next episode |

## 2. Chapter card (one per chapter)

```
CH 07 | 14:51–17:48 (177s) | "Rules first, or power first?"
INBOUND Q   : (what the last chapter left open)
ANSWER      : (one sentence this chapter establishes)
OUTBOUND Q  : (what this chapter leaves open — next chapter's inbound)
BRIDGE      : question | objection | zoom | callback | refrain
EVIDENCE    : [E12 archival clip] [E13 statute scan] [E14 number + source]
METAPHOR    : traffic light (rule known before vs after) → see metaphor card M05
CAMERA      : 2 stations, push-in on statute, whip to footage
RHYTHM      : case chapter — 3–8s shots, one hold on the statute
REFRAIN?    : no
PLANTS      : plants P3 ("red light / green light") — paid in CH 15
```

Rule: if a chapter's inbound and outbound questions are the same, it adds nothing. Merge or cut it.

## 3. Plant / payoff table

| ID | Planted (time, form) | Paid off (time, form) | Status |
|---|---|---|---|
| P1 | 00:42 insider quote, typeset | 30:28 same quote re-shown, decoded | ✓ |
| P2 | 00:00 "Are we short of money?" | 32:14 "Back to the opening question…" | ✓ |
| P3 | 14:51 traffic-light prop | 32:14 gauge trio callback | ✓ |

No orphan plants, and no payoff that wasn't planted.

## 4. Evidence ledger

```
ID   | line (VO)                         | type        | source                      | status
E01  | "Deposits exceed annual GDP."     | fact        | central bank stat, yyyy-mm  | verified
E02  | "Ninety percent just circulates." | quote       | named speaker, event, date  | attributed, not endorsed
E03  | "So prices stop telling truth."   | opinion     | —                           | thesis
E04  | ledger: borrow 3%, deposit 2%     | illustration| simplified                  | labelled on screen
```

On screen: facts show unit/date/source; quotes show speaker; illustrations show "simplified"/"illustrative". Opinion is allowed but must sound like the narrator's view, not a citation.

## 5. Bridge library

- **Question handoff**: "…what does that look like? Let's look at X."
- **Objection handoff**: "Someone will jump in: what about Y?" → next chapter opens "Good question."
- **Zoom handoff (out)**: a person's choice → "multiply that by a whole country."
- **Zoom handoff (in)**: a system number → "here is what it means for one person."
- **Callback handoff**: "Now we can finally explain what Z meant."
- **Refrain close**: end on the thesis phrase; next chapter opens on its consequence.
- **Answer-then-reopen**: answer the sub-question, then "but that raises a harder one."

Avoid "Next, let's talk about…" — that's a topic handoff and drops the open question.

## 6. Pacing bands by chapter function

| Function | Shot rhythm (ASL) | Camera | VO density |
|---|---|---|---|
| Cold open | 1–3s, bursts allowed | whips, flashes | high, punchy lines |
| Case / evidence | 3–8s | push-in on documents | high |
| Foundations | 6–12s | slow pans along a timeline | medium, slower rate |
| Mechanism | 15–60s, may be one move | continuous canvas travel | high |
| Steelman | 8–15s | footage ↔ diagram | medium |
| Reflection | 15–30s | slow drift, collage | lower, pauses allowed |

## 7. Worked breakdown — a measured 35-minute essay

Source: a 1080p30, 35:42 narrated economics essay with 18 YouTube chapters, paper-collage visuals, VO throughout. Measured with `scripts/shot-stats.py`, `sub-pacing.py`, `audio-stats.sh`, then checked visually on contact sheets. Subject details are omitted; the structure is what transfers.

| # | Start | Len | Function | ASL | Longest | Bridge out |
|---|---|---|---|---|---|---|
| 1 | 00:00 | 102s | Cold open → protagonist named | 4.1s (whip bursts) | 18s | names the protagonist |
| 2 | 01:42 | 159s | Protagonist case | 5.3s | 17s | **question**: "what is that thing in between? It's called finance" |
| 3 | 04:21 | 210s | Foundations (everyday loan → history) | 11.1s | 42s | **question**: "what does a computable credit system look like?" |
| 4 | 07:51 | 148s | Comparison with a popular belief | 5.5s | 16s | names the next concept |
| 5 | 10:19 | 107s | Named concept ("pawnshop thinking") | 4.9s | 23s | contrast line |
| 6 | 12:06 | 165s | Mechanism (credit pricing) | 18.3s | 65s | names the power at stake |
| 7 | 14:51 | 177s | Rules vs power | 7.7s | 32s | **objection**: "what about 2008?" |
| 8 | 17:48 | 143s | **Steelman** | 14.3s | 72s | names the next problem (implicit guarantee) |
| 9 | 20:11 | 64s | Consequence 1 | **no cut** | 64s+ | refrain: "prices stop telling the truth" |
| 10 | 21:15 | 164s | The bill reaches the everyman | 14.9s | 47s | refrain |
| 11 | 23:59 | 63s | **First answer** to central question | **no cut** | 110s take spans ch. 10–12 | zoom in on proposals |
| 12 | 25:02 | 100s | Proposal 1 | 12.5s | 35s | refrain |
| 13 | 26:42 | 123s | Proposals 2–4 | 8.8s | 29s | — |
| 14 | 28:45 | 103s | **Ensemble** (five rational actors) | 8.6s | 17s | "everyone's rational choice adds up to waste" |
| 15 | 30:28 | 106s | **Callback** to the opening quote | 35.3s | 57s | — |
| 16 | 32:14 | 73s | Resolution ("back to the opening question") | 10.4s | 21s | — |
| 17 | 33:27 | 78s | Reflection (nostalgia, period photos) | 15.6s | 32s | 1.9s silence |
| 18 | 34:45 | 57s | **Frame shift** + next episode | 14.2s | 40s | question |

ASL here is after merging cut bursts < 0.5s apart (whip-pans and handheld footage fool scene detection; see **reference-video-analysis**).

Whole-film numbers: 281 raw cuts → 213 after merging 11 bursts (ASL 10.0s, median 4.5s); narration covers 83.5% of the runtime at 4.95 CJK chars/s; 38 question lines; only 3 silences > 0.6s (longest 1.9s, right before the outro); −17.2 LUFS integrated, LRA 3.0 LU.

What transfers:

- Rhythm follows chapter function: hooks cut fast, mechanisms run long continuous moves (two chapters with zero hard cuts).
- The thesis refrain closes chapters 9, 10 and 12 and becomes the spine of the second half.
- The central question is answered twice, provisionally at ~67% and fully at ~90%, after the opening quote is decoded at ~85%.
- The steelman sits right after the strongest claim (rules vs power), introduced by an objection handoff.
- The only real silence is spent before the outro's frame shift.

---
Plant the question, hand it from chapter to chapter, and pay it off where the viewer can re-read the opening. Built by **[iart.ai](https://iart.ai/?utm_source=github&utm_medium=readme&utm_campaign=explainer-video-skills&utm_content=skill_footer&utm_term=longform-explainer)** — the AI motion agent for editable, on-brand motion graphics.
