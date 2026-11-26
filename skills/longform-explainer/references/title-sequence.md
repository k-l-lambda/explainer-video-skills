# Building a TV-style title sequence

From an 11-second title sequence for a 20-minute math explainer: thirteen shots of the field's history
in one engraving style, ending on a pull-back into "mathematical reality" and the film's title. SKILL.md
gives the principles (5–15 s, the film's own motifs, preview the conflict, borrow nothing); this is the
build.

## Where it goes

After the cold open's question, before the first chapter's answer. Let the question finish at the normal
gap after the line before it, cut hard into the title on the question's last word plus a breath (~0.6 s),
and cut hard out into the next line after ~1 s of the next shot. Anything that illustrated a word of the
question (a montage on "predecessors") stays on that word, before the title; it must not drift to after
it (**explainer-video** `references/production-qa.md` §4, re-timing checklist).

In the timeline, make the title a shot with its own anchor ("starts N s after line X ends") and a music
cue keyed to that shot; the chapter bed pauses around it (**ace-music**, mixing).

## Picking the nodes

- Choose events the film itself uses: every node should be recognisable later (a function, a theorem, a
  person who is named again). Check the list against the chapters; add the ones the film quotes (an
  agenda-setter, a programme named in the script) before famous ones it never mentions.
- 10–13 nodes for 8 s at 0.5 s each; give the central one 1 s and the turn to the present 1.5 s.
- Living people are not drawn as faces: silhouettes, hands, symbols, places.
- No text in the body; the title alone appears, set by the edit.

## Music first

Generate a few short cues in different directions, pick one, and **measure its accents** (**api-music**,
short cues). Then the shot list is a grid: one shot per accent, the hit on the reveal, the title after
the hit, the ring-out under the title. The picture follows the music, not the reverse.

## One style across generated frames

Write the style once (technique, material, palette, light, composition, no text) and append it to every
first-frame prompt (**create-image**, consistent set of frames). Generate all frames, review them as one
contact sheet, regenerate only the outliers with edits. Make the style change at the turn deliberately
(here engraving lines start to glow at the present-day shot and the last shots are light on dark).

## Still, clip or code per shot

At 0.5 s a shot is 15 frames. Most shots are stills with an eased move and beat-synced accents (the
accent colour extracted as a mask and pulsed on each accent). Generate clips only for continuous change
(lines turning into light, flying along a structure, the final pull-back). Draw exact mathematics in code
over a plate (the function's curve, its zeros flashing as it passes them). Unify everything with one
grain/vignette layer so stills and clips read as one material.

Moves: decide one grammar for the whole sequence (here: every zoom is a pull-back) and apply it to
stills and to the scale layered over clips; a clip whose own motion goes the other way can be reversed.

## Joining it to the film

- Fade into the final shot by holding its first frame for 4–8 frames before the hit and dissolving.
- Build it as its own composition (renderable alone with its music) and as a shot inside the film
  (music from the mix, not the component).
- Preview the stretch from the line before the question to ~3 s after the title, with the full mix.
