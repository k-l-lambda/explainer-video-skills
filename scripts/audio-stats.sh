#!/usr/bin/env bash
# audio-stats.sh — loudness + silence profile of a film's soundtrack.
#
# Prints integrated loudness (LUFS), loudness range (LRA), true peak, and every silence longer
# than a threshold. Use on a reference to learn how dense its VO/mix is, and on your own export
# to check it against the platform target (YouTube ≈ −14 LUFS; long VO pieces often −14…−16).
#
# Usage:
#   scripts/audio-stats.sh film.mp4                 # silences ≥ 0.6s below −35 dB
#   scripts/audio-stats.sh film.mp4 0.4 -40         # min silence 0.4s, floor −40 dB
# Needs: ffmpeg.
set -euo pipefail
in="${1:?usage: audio-stats.sh <file> [min_silence_s=0.6] [noise_db=-35]}"
d="${2:-0.6}"; n="${3:--35}"
log="$(mktemp)"; trap 'rm -f "$log"' EXIT
# ebur128 per-frame logging is silenced via -v; the Summary block is printed at level info
ffmpeg -hide_banner -nostats -i "$in" -vn \
  -af "silencedetect=noise=${n}dB:d=${d},ebur128=peak=true:framelog=verbose" -f null - 2>"$log" || true
I=$(grep -A2 "Integrated loudness" "$log" | sed -n 's/.*I: *\(-\?[0-9.]*\) LUFS.*/\1/p' | tail -1)
LRA=$(grep -A2 "Loudness range" "$log" | sed -n 's/.*LRA: *\([0-9.]*\) LU.*/\1/p' | tail -1)
TP=$(grep -A2 "True peak" "$log" | sed -n 's/.*Peak: *\(-\?[0-9.]*\) dBFS.*/\1/p' | tail -1)
printf '  %s\n  integrated %s LUFS · LRA %s LU · true peak %s dBFS\n' "$(basename "$in")" "${I:-?}" "${LRA:-?}" "${TP:-?}"
cnt=$(grep -c "silence_end" "$log" || true)
echo "  silences ≥ ${d}s below ${n} dB: ${cnt}"
grep "silence_end" "$log" | sed -n 's/.*silence_end: *\([0-9.]*\) | silence_duration: *\([0-9.]*\).*/\1 \2/p' |
  awk '{s=$1-$2; printf "    %02d:%04.1f  %.1fs\n", int(s/60), s-int(s/60)*60, $2}' | sort -k2 -rn | head -15
