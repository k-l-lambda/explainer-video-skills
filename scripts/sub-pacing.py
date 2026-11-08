#!/usr/bin/env python3
"""sub-pacing.py — narration pacing from a subtitle file (.vtt / .srt).

Reports speech rate (CJK chars/s and Latin words/min), narration coverage, pauses, question
lines, and per-chapter density + how each chapter opens and closes (does it end on a question?).
Use it to measure a reference film's script rhythm, or to check your own VO against the plan.

Usage:
  python scripts/sub-pacing.py film.zh.vtt
  python scripts/sub-pacing.py film.en.vtt --chapters film.info.json   # yt-dlp metadata
  python scripts/sub-pacing.py out/captions.srt --chapters chapters.tsv --gap 1.0

Notes:
  * YouTube auto-captions repeat rolling lines; consecutive duplicate cues are merged.
  * Coverage = time covered by cues / span. It overestimates speech if cues are padded.
Standard library only.
"""
import argparse, json, re

TS = r"(?:(\d+):)?(\d+):(\d+)[.,](\d+)"
CJK = re.compile(r"[㐀-鿿豈-﫿぀-ヿ가-힯]")
WORD = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")
QMARK = re.compile(r"[?？]")


def secs(h, m, s, frac):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + float("0." + frac)


def parse_subs(path):
    text = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text):
        m = re.search(TS + r"\s*-->\s*" + TS, block)
        if not m:
            continue
        a, b = secs(*m.groups()[:4]), secs(*m.groups()[4:])
        body = block[m.end():].split("\n", 1)[1] if "\n" in block[m.end():] else ""
        body = re.sub(r"<[^>]+>|\{[^}]+\}", "", body).strip()
        if not body:
            continue
        if cues and body == cues[-1][2]:              # rolling duplicate
            cues[-1] = (cues[-1][0], max(b, cues[-1][1]), body)
            continue
        cues.append((a, b, body))
    return cues


def parse_ts(s):
    v = 0.0
    for p in s.strip().split(":"):
        v = v * 60 + float(p)
    return v


def load_chapters(path, end):
    if path.endswith(".json"):
        ch = [(c["start_time"], c.get("end_time"), c.get("title", ""))
              for c in json.load(open(path, encoding="utf-8")).get("chapters") or []]
    else:
        ch = []
        for line in open(path, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                ts, _, title = line.rstrip("\n").partition("\t")
                ch.append((parse_ts(ts), None, title))
    return [(s, e if e is not None else (ch[i + 1][0] if i + 1 < len(ch) else end), t)
            for i, (s, e, t) in enumerate(ch)]


def units(cues):
    txt = " ".join(c[2] for c in cues)
    return len(CJK.findall(txt)), len(WORD.findall(CJK.sub(" ", txt)))


def rate(cjk, words, span):
    # report the dominant script; show the other only for genuinely mixed text
    # (digits/acronyms inside CJK narration would otherwise show up as a bogus words/min)
    parts = []
    if cjk and cjk >= words / 2:
        parts.append(f"{cjk / span:.2f} CJK chars/s")
    if words and (not parts or words > cjk / 3):
        parts.append(f"{words / span * 60:.0f} words/min")
    return " · ".join(parts) or "no text"


def fmt(t):
    return f"{int(t) // 60:02d}:{t % 60:04.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("subs")
    ap.add_argument("--chapters", help="yt-dlp .info.json or TSV of 'mm:ss<TAB>title'")
    ap.add_argument("--gap", type=float, default=0.6, help="report pauses longer than this (s)")
    ap.add_argument("--edge", type=int, default=2, help="cues shown at each chapter's start/end")
    a = ap.parse_args()

    cues = parse_subs(a.subs)
    if not cues:
        raise SystemExit("no cues parsed")
    t0, t1 = cues[0][0], cues[-1][1]
    span = t1 - t0
    covered = sum(b - a_ for a_, b, _ in cues)
    cjk, words = units(cues)
    gaps = [(cues[i][1], cues[i + 1][0] - cues[i][1]) for i in range(len(cues) - 1)
            if cues[i + 1][0] - cues[i][1] > a.gap]
    qs = [c for c in cues if QMARK.search(c[2])]

    print(f"{a.subs}: {len(cues)} cues  span {fmt(t0)}–{fmt(t1)} ({span:.0f}s)")
    print(f"  rate {rate(cjk, words, span)}  (over cue time only: {rate(cjk, words, covered)})")
    print(f"  coverage {covered / span:.1%}  pauses >{a.gap}s: {len(gaps)}  question lines: {len(qs)}")
    for at, g in sorted(gaps, key=lambda x: -x[1])[:10]:
        print(f"    pause {g:4.1f}s at {fmt(at)}")

    if a.chapters:
        print("  per chapter (Q = question lines; '→?' = chapter closes on a question):")
        for s, e, title in load_chapters(a.chapters, t1):
            cc = [c for c in cues if s <= c[0] < e]
            if not cc:
                continue
            cj, w = units(cc)
            q = sum(1 for c in cc if QMARK.search(c[2]))
            tail = cc[-a.edge:]
            ends_q = "→?" if any(QMARK.search(c[2]) for c in tail) else "  "
            print(f"    {fmt(s)} {e - s:5.0f}s  {rate(cj, w, e - s):>22}  Q={q:<2} {ends_q}  {title[:40]}")
            print(f"        open : {' / '.join(c[2] for c in cc[:a.edge])[:90]}")
            print(f"        close: {' / '.join(c[2] for c in tail)[-90:]}")


if __name__ == "__main__":
    main()
