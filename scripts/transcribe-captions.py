#!/usr/bin/env python3
"""Word-timed transcript of a narration file as Remotion Caption[] JSON, with faster-whisper.

    python scripts/transcribe-captions.py s2.wav s2.captions.json [--model small] [--language zh] [--device auto]

Each word becomes {text, startMs, endMs, timestampMs, confidence}, the shape @remotion/captions
uses. Whisper makes homophone errors: compare the text with the script and fix words in the JSON
(or later in Studio's captions inspector); the timings are what matter here.
"""
import argparse
import json

from faster_whisper import WhisperModel

parser = argparse.ArgumentParser()
parser.add_argument('audio')
parser.add_argument('out')
parser.add_argument('--model', default='small', help='faster-whisper size or path (base, small, medium, large-v3)')
parser.add_argument('--language', default=None, help='e.g. zh, en; default: detect')
parser.add_argument('--device', default='auto', help='auto, cuda or cpu')
args = parser.parse_args()

model = WhisperModel(args.model, device=args.device, compute_type='default')
segments, info = model.transcribe(args.audio, language=args.language, word_timestamps=True)
captions = []
for segment in segments:
    for word in segment.words:
        captions.append({'text': word.word, 'startMs': round(word.start * 1000), 'endMs': round(word.end * 1000),
                         'timestampMs': round((word.start + word.end) * 500), 'confidence': round(word.probability, 3)})
with open(args.out, 'w', encoding='utf-8') as f:
    json.dump(captions, f, ensure_ascii=False, indent=1)
print(json.dumps({'out': args.out, 'words': len(captions), 'seconds': info.duration, 'language': info.language,
                  'text': ''.join(c['text'] for c in captions)}, ensure_ascii=False))
