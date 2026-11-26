#!/usr/bin/env python3
"""Generate music through an HTTP music API with the ElevenLabs music contract (plan / compose / detailed).

Every compose call is billed and returns finished audio in one synchronous response (no task to poll, nothing
to cancel). The plan call writes only a composition plan (JSON) and is cheap, so the intended loop is:
plan -> edit the plan -> compose from the plan.

The gateway's base URL, path prefix, key and model id are NOT in this file. They come from config.local.json
next to this skill's SKILL.md (not committed; see doc.local.md), or from the flags/env below.

Usage:
    genmusic.py plan    --prompt-file P.txt --length 60 -o plan.json
    genmusic.py compose --prompt-file P.txt --length 60 -o out.mp3 [--instrumental] [--detailed]
    genmusic.py compose --plan plan.json -o out.wav [--detailed]      # .wav: asks for PCM and wraps it
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import wave

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(HERE, 'config.local.json')
TIMEOUT = 900          # long tracks (3 min) came back in ~12 s, but leave room
PCM_RATE = 48000       # output_format=pcm_<rate>: 16-bit little-endian, stereo


def load_config(a):
	cfg = {}
	if os.path.exists(CONFIG):
		cfg = json.load(open(CONFIG))
	base = a.base_url or os.environ.get(cfg.get('base_url_env', ''), '') or cfg.get('base_url', '')
	key = os.environ.get(a.key_env or cfg.get('key_env', ''), '')
	prefix = a.prefix or cfg.get('prefix', '')
	model = a.model or cfg.get('model_id', '')
	missing = [n for n, v in (('base url', base), ('api key', key), ('path prefix', prefix), ('model id', model)) if not v]
	if missing:
		raise SystemExit('genmusic: missing %s; write %s (see doc.local.md) or pass the flags' % (', '.join(missing), CONFIG))
	return base.rstrip('/') + '/' + prefix.strip('/'), key, model


def post(url, key, body):
	req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST',
		headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
	t0 = time.time()
	try:
		with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
			return res.read(), dict(res.headers), time.time() - t0
	except urllib.error.HTTPError as err:
		detail = err.read().decode('utf-8', 'replace')
		hint = ''
		if 'unsupported native endpoint contract' in detail:
			hint = '\n(the gateway gives this for a body it does not accept, e.g. without model_id; the path may be fine)'
		raise SystemExit('genmusic: HTTP %d\n%s%s' % (err.code, detail[:2000], hint))


def split_multipart(raw, ctype):
	"""/detailed returns multipart/mixed: a JSON part (plan + metadata), then the audio part."""
	b = re.search(r'boundary="?([^";]+)"?', ctype).group(1).encode()
	meta, audio = None, None
	for part in raw.split(b'--' + b):
		head, sep, body = part.partition(b'\r\n\r\n')
		if not sep:
			head, sep, body = part.partition(b'\n\n')
		if not sep:
			continue
		body = body[:-2] if body.endswith(b'\r\n') else body
		if b'application/json' in head:
			meta = json.loads(body)
		elif b'audio/' in head:
			audio = body
	if audio is None:
		raise SystemExit('genmusic: no audio part in the multipart response')
	return meta, audio


def body_from(a, model):
	body = {'model_id': model}
	if a.plan:
		plan = json.load(open(a.plan))
		body['composition_plan'] = plan.get('composition_plan', plan)   # accepts a /detailed metadata file too
	else:
		text = open(a.prompt_file).read().strip() if a.prompt_file else a.prompt
		if not text:
			raise SystemExit('genmusic: give --prompt, --prompt-file or --plan')
		body['prompt'] = text
		if a.length:
			body['music_length_ms'] = int(a.length * 1000)
	if getattr(a, 'instrumental', False):
		if a.plan:   # HTTP 422 "`force_instrumental` can only be used with `prompt`."
			print('genmusic: --instrumental ignored with --plan; put "vocals" in each chunk\'s negative_styles', file=sys.stderr)
		else:
			body['force_instrumental'] = True
	return body


def main():
	ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
	ap.add_argument('cmd', choices=('plan', 'compose'))
	ap.add_argument('-o', '--out', required=True)
	ap.add_argument('--prompt')
	ap.add_argument('--prompt-file')
	ap.add_argument('--plan', help='composition plan JSON (from `plan`, or a /detailed metadata file)')
	ap.add_argument('--length', type=float, help='seconds (prompt mode; a plan carries its own durations)')
	ap.add_argument('--instrumental', action='store_true', help='force_instrumental: no vocals')
	ap.add_argument('--detailed', action='store_true', help='also save the plan the model used, as OUT.json')
	ap.add_argument('--base-url'); ap.add_argument('--key-env'); ap.add_argument('--prefix'); ap.add_argument('--model')
	ap.add_argument('--dry-run', action='store_true', help='print the request and exit; nothing is billed')
	a = ap.parse_args()

	root, key, model = load_config(a)
	body = body_from(a, model)
	if a.cmd == 'plan':
		body.pop('force_instrumental', None)
		url = root + '/music/plan'
	else:
		url = root + ('/music/detailed' if a.detailed else '/music')
		if a.out.lower().endswith('.wav'):
			url += '?output_format=pcm_%d' % PCM_RATE
	if a.dry_run:
		print('POST', re.sub(r'^https?://[^/]+', '<base>', url))
		print(json.dumps(body, ensure_ascii=False, indent=1)[:3000])
		return

	raw, headers, secs = post(url, key, body)
	ctype = headers.get('Content-Type', headers.get('content-type', ''))
	if a.cmd == 'plan':
		plan = json.loads(raw)
		json.dump(plan, open(a.out, 'w'), ensure_ascii=False, indent=1)
		total = sum(c['duration_ms'] for c in plan['chunks']) / 1000
		print('plan: %d sections, %.1f s, in %.1f s -> %s' % (len(plan['chunks']), total, secs, a.out))
		for c in plan['chunks']:
			print('  %-24s %5.1f s  %s' % (c['text'], c['duration_ms'] / 1000, ', '.join(c['positive_styles'][:4])))
		return

	meta = None
	if ctype.startswith('multipart/'):
		meta, raw = split_multipart(raw, ctype)
	if a.out.lower().endswith('.wav'):
		with wave.open(a.out, 'wb') as w:
			w.setnchannels(2); w.setsampwidth(2); w.setframerate(PCM_RATE); w.writeframes(raw)
	else:
		open(a.out, 'wb').write(raw)
	if meta is not None:
		side = os.path.splitext(a.out)[0] + '.json'
		json.dump(meta, open(side, 'w'), ensure_ascii=False, indent=1)
		print('plan used ->', side)
	song = headers.get('song-id') or headers.get('Song-Id') or ''
	print('%s: %d B in %.1f s%s -> %s' % (a.cmd, len(raw), secs, ('  song-id ' + song) if song else '', a.out))


if __name__ == '__main__':
	main()
