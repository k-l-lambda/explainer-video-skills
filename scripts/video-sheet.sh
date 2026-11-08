#!/usr/bin/env bash
# video-sheet.sh — timestamped contact sheet straight from a video segment.
#
# Samples one frame every STEP seconds from START, stamps the timecode on each, and tiles them
# into one image (default 4x3 = 12 frames, 400px wide each → 1600px sheet, safe for image-reading
# agents). Use it to *look* at what the numbers point to: a burst, a long take, a chapter boundary.
#
# Usage:
#   scripts/video-sheet.sh film.mp4 sheet.jpg 1260 2        # 12 frames from 21:00, every 2s
#   scripts/video-sheet.sh film.mp4 burst.jpg 33.8 0.4      # dense look at a cut burst
#   scripts/video-sheet.sh film.mp4 all.jpg 0 auto 6x5      # whole film, 30 evenly spaced frames
# Args: <video> <out.jpg> [start_s=0] [step_s|auto=1] [COLSxROWS=4x3] [tile_width=400]
# Needs: ffmpeg/ffprobe built with drawtext (libfreetype); falls back to no timestamps otherwise.
set -euo pipefail
in="${1:?usage: video-sheet.sh <video> <out.jpg> [start] [step|auto] [CxR] [width]}"
out="${2:?need output path}"; start="${3:-0}"; step="${4:-1}"; grid="${5:-4x3}"; w="${6:-400}"
cols="${grid%x*}"; rows="${grid#*x}"; count=$((cols * rows))
# accept hh:mm:ss / mm:ss starts, but use plain seconds below (a ':' would break drawtext)
start=$(awk -v s="$start" 'BEGIN{n=split(s,p,":"); v=0; for(i=1;i<=n;i++) v=v*60+p[i]; printf "%.3f", v}')
if [ "$step" = auto ]; then
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
  step=$(awk -v d="$dur" -v s="$start" -v n="$count" 'BEGIN{printf "%.3f", (d-s)/n}')
fi
stamp="drawtext=text='%{pts\\:hms\\:${start}}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6"
base="fps=1/${step},scale=${w}:-2"
if ! ffmpeg -hide_banner -loglevel error -y -ss "$start" -i "$in" \
     -vf "${base},${stamp},tile=${grid}" -frames:v 1 "$out" 2>/dev/null; then
  echo "  ⚠ drawtext unavailable — sheet without timestamps (frame k is at start + k*step)"
  ffmpeg -hide_banner -loglevel error -y -ss "$start" -i "$in" -vf "${base},tile=${grid}" -frames:v 1 "$out"
fi
echo "  ✓ ${count} frames from ${start}s every ${step}s → $out"
