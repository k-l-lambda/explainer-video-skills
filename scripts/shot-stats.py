#!/usr/bin/env python3
"""shot-stats.py — cut rhythm of a video: cuts, average shot length (ASL), bursts, long takes.

Runs ffmpeg scene detection once (cached to <video>.cuts.txt), then reports whole-film and
per-chapter rhythm. Use it on a reference film to learn its pacing, and on your own render to
check yours against the plan.

Usage:
  python scripts/shot-stats.py film.mp4
  python scripts/shot-stats.py film.mp4 --chapters film.info.json     # yt-dlp metadata
  python scripts/shot-stats.py film.mp4 --chapters chapters.tsv       # "mm:ss<TAB>title" per line
  python scripts/shot-stats.py film.mp4 --threshold 0.25 --burst 0.5 --top 8

Caveats (verify on a contact sheet before concluding anything):
  * whip-pans, flashes and fast blur produce clusters of false "cuts" -> reported as bursts;
  * slow dissolves and continuous camera moves produce no cuts -> a long "shot" may be
    one continuous move across a canvas, not a static hold.
Needs: ffmpeg + ffprobe on PATH. Standard library only.
"""
import argparse, json, os, re, statistics, subprocess, sys


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def detect_cuts(path, threshold, cache):
    if os.path.exists(cache):
        return [float(x) for x in open(cache) if x.strip()]
    # downscale for speed; showinfo prints pts_time for every selected (scene-change) frame
    vf = f"scale=480:-2,select='gt(scene\\,{threshold})',showinfo"
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf", vf,
                           "-f", "null", "-"], capture_output=True, text=True)
    cuts = [float(m) for m in re.findall(r"pts_time:([\d.]+)", proc.stderr)]
    if proc.returncode != 0 and not cuts:
        sys.exit(proc.stderr[-2000:])
    with open(cache, "w") as f:
        f.write("\n".join(f"{c:.3f}" for c in cuts))
    return cuts


def parse_ts(s):
    parts = [float(p) for p in s.strip().split(":")]
    v = 0.0
    for p in parts:
        v = v * 60 + p
    return v


def load_chapters(path, duration):
    if path.endswith(".json"):
        d = json.load(open(path, encoding="utf-8"))
        ch = [(c["start_time"], c.get("end_time"), c.get("title", "")) for c in d.get("chapters") or []]
    else:
        rows = []
        for line in open(path, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                ts, _, title = line.rstrip("\n").partition("\t")
                rows.append((parse_ts(ts), None, title))
        ch = rows
    out = []
    for i, (s, e, t) in enumerate(ch):
        e = e if e is not None else (ch[i + 1][0] if i + 1 < len(ch) else duration)
        out.append((s, e, t))
    return out


def merge_bursts(cuts, gap):
    """Collapse cuts closer than `gap` seconds into one event; return (events, bursts)."""
    events, bursts, run = [], [], []
    for c in cuts:
        if run and c - run[-1] < gap:
            run.append(c)
            continue
        if len(run) >= 3:
            bursts.append((run[0], run[-1], len(run)))
        if run:
            events.append(run[0])
        run = [c]
    if run:
        events.append(run[0])
        if len(run) >= 3:
            bursts.append((run[0], run[-1], len(run)))
    return events, bursts


def shots(cuts, start, end):
    edges = [start] + [c for c in cuts if start < c < end] + [end]
    return [(a, b - a) for a, b in zip(edges, edges[1:]) if b > a]


def fmt(t):
    return f"{int(t) // 60:02d}:{t % 60:04.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("video")
    ap.add_argument("--chapters", help="yt-dlp .info.json or TSV of 'mm:ss<TAB>title'")
    ap.add_argument("--threshold", type=float, default=0.30, help="ffmpeg scene score (0.2–0.4)")
    ap.add_argument("--burst", type=float, default=0.5, help="cuts closer than this (s) merge into a burst")
    ap.add_argument("--top", type=int, default=6, help="how many longest takes to list")
    ap.add_argument("--json", help="also write results to this JSON file")
    a = ap.parse_args()

    dur = probe_duration(a.video)
    cache = f"{a.video}.cuts-{a.threshold:.2f}.txt"
    raw = detect_cuts(a.video, a.threshold, cache)
    events, bursts = merge_bursts(raw, a.burst)
    sh = shots(events, 0.0, dur)
    lens = sorted(l for _, l in sh)
    q = lambda p: lens[min(len(lens) - 1, int(len(lens) * p))]

    print(f"{os.path.basename(a.video)}  {fmt(dur)}  threshold={a.threshold}  (cache: {cache})")
    print(f"  raw cuts {len(raw)} -> {len(events)} events after merging {len(bursts)} burst(s) (<{a.burst}s apart)")
    print(f"  shots {len(sh)}  ASL {dur / len(sh):.2f}s  median {statistics.median(lens):.2f}s"
          f"  p10 {q(.1):.2f}s  p90 {q(.9):.2f}s  max {lens[-1]:.1f}s")
    if bursts:
        print("  bursts (likely whip/flash/blur, check visually):")
        for s, e, n in bursts[:12]:
            print(f"    {fmt(s)}–{fmt(e)}  {n} raw cuts")
    print(f"  longest takes (continuous move or hold, check visually):")
    for s, l in sorted(sh, key=lambda x: -x[1])[:a.top]:
        print(f"    {fmt(s)}  {l:5.1f}s")

    result = {"duration": dur, "raw_cuts": raw, "events": events, "bursts": bursts,
              "asl": dur / len(sh), "median": statistics.median(lens), "chapters": []}
    if a.chapters:
        print("  per chapter:")
        for s, e, title in load_chapters(a.chapters, dur):
            n = sum(1 for c in events if s < c < e)
            cs = shots(events, s, e)
            longest = max(l for _, l in cs)
            print(f"    {fmt(s)}  {e - s:6.0f}s  cuts {n:3d}  ASL {(e - s) / (n + 1):5.1f}s"
                  f"  longest {longest:5.1f}s  {title[:40]}")
            result["chapters"].append({"start": s, "end": e, "title": title, "cuts": n,
                                       "asl": (e - s) / (n + 1), "longest": longest})
    if a.json:
        json.dump(result, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
