#!/usr/bin/env python3
"""Generate images through the proxy's gpt-image-2 endpoint.

Why this exists as a script rather than a curl line: the endpoint takes long
prompts full of hex codes, quotes and backticks, which a shell mangles, and it
returns a *signed URL* rather than image bytes, so every generation is two
steps. Both mistakes are easy to make once and hard to notice, because a
mangled prompt still produces a perfectly nice picture of the wrong thing.

Usage:
    tools/genimage.py PROMPT_FILE OUT.png [--quality high] [--size 1024x1024]
    tools/genimage.py PROMPT_FILE OUT.png --n 4        # OUT-1.png .. OUT-4.png
    echo "a red ball" | tools/genimage.py - out.png

The prompt is read from a file (or stdin as `-`) on purpose. Prompts for this
project run to several hundred words and carry exact colour values; keeping them
in files means they can be diffed and reused, and it keeps the shell out of
them.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

# The origin comes from the environment so this script follows whichever proxy
# the session is configured against, instead of pinning a host that will
# eventually be wrong.
BASE_URL = os.environ.get('CLAUDE_BASE_URL', '').rstrip('/')
MODEL = 'gpt-image-2-text-to-image'
EDIT_MODEL = 'gpt-image-2-edit'

# Only these are accepted; the server rejects anything else with a 400 that
# quotes the whole schema back. Kept here so a typo fails locally and instantly
# rather than after a round trip.
SIZES = (
	'1024x1024', '1024x1536', '1536x1024', '2048x2048', '2048x1152',
	'3840x2160', '2160x3840', '2048x1360', '1360x2048', '1152x2048',
	'2048x1536', '1536x2048', '2048x880', '880x2048', '688x2048',
	'2048x688', '2048x1024', '1024x2048', 'auto',
)
QUALITIES = ('low', 'medium', 'high')
FORMATS = ('png', 'jpeg')
BACKGROUNDS = ('opaque', 'auto')
MAX_PROMPT = 32000

# High quality takes around two and a half minutes for one 1024px image, so the
# socket timeout has to be generous or a good generation dies in transit.
TIMEOUT = 600


def read_prompt (path):
	"""Read the prompt from a file, or from stdin when path is '-'."""
	text = sys.stdin.read() if path == '-' else open(path, encoding='utf-8').read()
	text = text.strip()

	if not text:
		raise SystemExit('genimage: prompt is empty (the server rejects an empty prompt)')
	if len(text) > MAX_PROMPT:
		raise SystemExit('genimage: prompt is %d chars, the limit is %d' % (len(text), MAX_PROMPT))

	return text


def encode_image (path):
	"""Read an image for the edit endpoint.

	An http(s) URL is passed through untouched; a local file becomes bare base64.
	The endpoint accepts bare base64, a `data:` URI and a URL, so the simplest
	form that works is used.
	"""
	if path.startswith('http://') or path.startswith('https://'):
		return path

	with open(path, 'rb') as fh:
		return base64.b64encode(fh.read()).decode('ascii')


def request_images (payload, key, model=MODEL):
	"""POST the payload and return the list of image URLs."""
	req = urllib.request.Request(
		'%s/v3/%s' % (BASE_URL, model),
		data=json.dumps(payload).encode('utf-8'),
		headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
		method='POST')

	try:
		with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
			body = json.loads(res.read())
	except urllib.error.HTTPError as err:
		detail = err.read().decode('utf-8', 'replace')
		raise SystemExit('genimage: HTTP %d\n%s' % (err.code, detail[:2000]))

	# Two response shapes come back from this endpoint. One carries `base_resp`
	# with a status code; the other omits it entirely and echoes the parameters
	# that were actually used. So `images` is the success signal -- keying off
	# `base_resp` reports a perfectly good image as a failure.
	status = body.get('base_resp', {}).get('status_code', 0)
	if status:
		raise SystemExit('genimage: server reported status %s: %s'
			% (status, body.get('base_resp', {}).get('status_msg', '')))

	urls = body.get('images') or []
	if not urls:
		raise SystemExit('genimage: no images in response: %s' % json.dumps(body)[:800])

	echoed = {k: v for k, v in body.items() if k not in ('images', 'base_resp')}
	if echoed:
		print('  server used: %s' % json.dumps(echoed, sort_keys=True), file=sys.stderr)

	return urls


def download (url, out):
	"""Fetch one generated image to disk.

	The URL is a time-signed object-store link, so it has to be fetched now
	rather than recorded for later.
	"""
	with urllib.request.urlopen(url, timeout=TIMEOUT) as res:
		data = res.read()

	with open(out, 'wb') as fh:
		fh.write(data)

	return len(data)


def main ():
	ap = argparse.ArgumentParser(description='Generate images via gpt-image-2.')
	ap.add_argument('prompt_file', help="file holding the prompt, or '-' for stdin")
	ap.add_argument('out', help='output path; with --n above 1, a -N suffix is added')
	ap.add_argument('--size', default='1024x1024', choices=SIZES)
	ap.add_argument('--quality', default='high', choices=QUALITIES,
		help='low is fastest and cheapest, high is slowest (default: high)')
	ap.add_argument('--format', dest='output_format', default='png', choices=FORMATS)
	ap.add_argument('--background', default='opaque', choices=BACKGROUNDS,
		help="neither value gives transparency; this endpoint cannot produce an alpha channel")
	ap.add_argument('--n', type=int, default=1, choices=range(1, 11), metavar='1-10',
		help='how many variants to ask for in one call (default: 1)')
	ap.add_argument('--compression', type=int, default=None, metavar='0-100',
		help='jpeg only; png must be 100 or unset')
	ap.add_argument('--edit', action='append', metavar='IMAGE',
		help='edit an existing image (local path or URL) instead of generating from '
			'text; repeat to pass several reference images')
	ap.add_argument('--mask', metavar='PNG',
		help='edit only where this PNG is fully transparent; requires an alpha channel')
	args = ap.parse_args()

	if not BASE_URL:
		raise SystemExit('genimage: CLAUDE_BASE_URL is not set')

	key = os.environ.get('PAIGOD_API_KEY')
	if not key:
		raise SystemExit('genimage: PAIGOD_API_KEY is not set')

	if args.compression is not None and args.output_format != 'jpeg':
		raise SystemExit('genimage: --compression applies to jpeg only')

	if args.mask and not args.edit:
		raise SystemExit('genimage: --mask only applies with --edit')

	prompt = read_prompt(args.prompt_file)

	payload = {
		'prompt': prompt,
		'size': args.size,
		'quality': args.quality,
		'output_format': args.output_format,
		'background': args.background,
		'n': args.n,
	}
	if args.compression is not None:
		payload['output_compression'] = args.compression

	model = MODEL
	if args.edit:
		model = EDIT_MODEL
		# A single image may be sent as a string or a one-item array; several
		# reference images go as an array.
		images = [encode_image(p) for p in args.edit]
		payload['image'] = images[0] if len(images) == 1 else images
		if args.mask:
			payload['mask'] = encode_image(args.mask)

	what = 'editing' if args.edit else 'generating'
	print('%s %d image(s), %s %s, %d chars of prompt'
		% (what, args.n, args.size, args.quality, len(prompt)), file=sys.stderr)

	urls = request_images(payload, key, model)

	# The server may return fewer images than requested, so name outputs from
	# what actually arrived rather than from what was asked for.
	if len(urls) < args.n:
		print('  note: asked for %d, received %d' % (args.n, len(urls)), file=sys.stderr)

	root, ext = os.path.splitext(args.out)
	if not ext:
		ext = '.' + args.output_format

	written = []
	for i, url in enumerate(urls, start=1):
		out = args.out if len(urls) == 1 else '%s-%d%s' % (root, i, ext)
		size = download(url, out)
		print('  wrote %s (%.0f KB)' % (out, size / 1024))
		written.append(out)

	return 0 if written else 1


if __name__ == '__main__':
	sys.exit(main())
