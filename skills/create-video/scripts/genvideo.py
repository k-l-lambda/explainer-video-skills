#!/usr/bin/env python3
"""Generate video through the proxy's Dreamina Seedance endpoint.

Video generation is asynchronous, which is the whole reason this script exists:
creating a task and receiving a video are two different calls separated by
minutes. A task cannot be cancelled once created -- the API exposes create and
poll and nothing else -- so a mistaken call cannot be taken back, and the script
is deliberately built to make one considered request rather than to sweep over
options.

Usage:
    tools/genvideo.py PROMPT_FILE OUT.mp4 [--duration 5] [--ratio 1:1] [--resolution 720p]
    tools/genvideo.py PROMPT_FILE OUT.mp4 --first-frame COVER.png
    tools/genvideo.py --task cgt-...        # poll or fetch an existing task
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get('CLAUDE_BASE_URL', '').rstrip('/')
PATH = '/v3/bytedance/metered/contents/generations/tasks'
MODEL = 'dreamina-seedance-2-5-260628'

# Ratio and resolution are NOT validated before work begins: an invalid value is
# refused for free, but a valid one starts a real generation that bills and
# cannot be cancelled. So the accepted values are listed here and checked
# locally, and nothing in this script loops over them.
RATIOS = ('1:1', '16:9', '9:16', '4:3', '3:4', '21:9', 'adaptive')
RESOLUTIONS = ('480p', '720p', '1080p')
DURATION_RANGE = (4, 30)

TERMINAL = ('succeeded', 'failed', 'cancelled', 'expired')
TIMEOUT = 120
POLL_SECONDS = 15
POLL_LIMIT = 80          # 80 x 15s == 20 minutes


def call (url, key, payload=None):
	req = urllib.request.Request(
		url,
		data=json.dumps(payload).encode('utf-8') if payload is not None else None,
		headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'},
		method='POST' if payload is not None else 'GET')

	try:
		with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
			return json.loads(res.read())
	except urllib.error.HTTPError as err:
		detail = err.read().decode('utf-8', 'replace')
		raise SystemExit('genvideo: HTTP %d\n%s' % (err.code, detail[:2000]))


def data_url (path):
	"""A local image as a data URL.

	The service will fetch an `http(s)` URL, but a file on this disk has no URL,
	and uploading it somewhere first would publish artwork to a third party to
	no purpose. Base64 in the request body keeps it between here and the API.
	"""
	kind = mimetypes.guess_type(path)[0] or 'image/png'
	with open(path, 'rb') as fh:
		return 'data:%s;base64,%s' % (kind, base64.b64encode(fh.read()).decode('ascii'))


def create (prompt, key, duration, ratio, resolution, audio, first_frame=None):
	"""Create one generation task and return its id.

	Parameters travel two different ways in this API, which is easy to get
	wrong: ratio and resolution are `--flag value` pairs appended to the prompt
	text, while duration and generate_audio are real JSON fields.

	A first frame is a second `content` part. It also silently changes what the
	other parameters may say: with a first frame the output ratio is taken from
	the image, and stating `--ratio` as well is rejected outright with
	`InvalidParameter.TaskTypeConstraint`. So the flag is dropped from the
	prompt text in that case rather than passed and hoped for.
	"""
	text = '%s --resolution %s' % (prompt, resolution)
	if not first_frame:
		text = '%s --ratio %s --resolution %s' % (prompt, ratio, resolution)

	content = [{'type': 'text', 'text': text}]
	if first_frame:
		content.append({'type': 'image_url', 'image_url': {'url': data_url(first_frame)}})

	payload = {
		'model': MODEL,
		'content': content,
		'duration': duration,
		'generate_audio': audio,
	}

	body = call(BASE_URL + PATH, key, payload)
	task = body.get('id')
	if not task:
		raise SystemExit('genvideo: no task id in response: %s' % json.dumps(body)[:800])

	return task


def status (task, key):
	return call('%s%s/%s' % (BASE_URL, PATH, task), key)


def video_url (body):
	"""Pull the finished video URL out of a completed task.

	The field is looked up rather than assumed, because a wrong guess here would
	silently report success while writing nothing.
	"""
	content = body.get('content')
	if isinstance(content, dict):
		for k in ('video_url', 'url', 'download_url'):
			if content.get(k):
				return content[k]
	if isinstance(content, list):
		for part in content:
			if isinstance(part, dict):
				for k in ('video_url', 'url', 'download_url'):
					if part.get(k):
						return part[k]
	for k in ('video_url', 'url', 'download_url'):
		if body.get(k):
			return body[k]

	return None


def download (url, out):
	with urllib.request.urlopen(url, timeout=600) as res:
		data = res.read()

	with open(out, 'wb') as fh:
		fh.write(data)

	return len(data)


def wait (task, key):
	"""Poll until the task reaches a terminal state, reporting as it goes."""
	for _ in range(POLL_LIMIT):
		body = status(task, key)
		state = body.get('status', '?')
		if state in TERMINAL:
			return body

		print('  %s ...' % state, file=sys.stderr)
		time.sleep(POLL_SECONDS)

	raise SystemExit('genvideo: %s still unfinished after %d minutes; poll it later with --task %s'
		% (task, POLL_LIMIT * POLL_SECONDS // 60, task))


def finish (body, out, task):
	state = body.get('status')
	if state != 'succeeded':
		raise SystemExit('genvideo: task %s ended as %s\n%s'
			% (task, state, json.dumps(body)[:1200]))

	url = video_url(body)
	if not url:
		raise SystemExit('genvideo: task succeeded but no video URL was found in:\n%s'
			% json.dumps(body, indent=2)[:1500])

	if not out:
		print(url)
		return 0

	size = download(url, out)
	print('  wrote %s (%.1f MB)' % (out, size / 1048576))

	return 0


def main ():
	ap = argparse.ArgumentParser(description='Generate video via Dreamina Seedance.')
	ap.add_argument('prompt_file', nargs='?', help="file holding the prompt, or '-' for stdin")
	ap.add_argument('out', nargs='?', help='output .mp4 path')
	ap.add_argument('--task', help='poll an existing task id instead of creating one')
	ap.add_argument('--duration', type=int, default=5,
		help='seconds, -1 or %d-%d (default: 5)' % DURATION_RANGE)
	ap.add_argument('--ratio', default='1:1', choices=RATIOS)
	ap.add_argument('--resolution', default='720p', choices=RESOLUTIONS)
	ap.add_argument('--audio', action='store_true',
		help='generate an audio track; off by default, since the API defaults it on')
	ap.add_argument('--first-frame', metavar='IMAGE',
		help='local image to start the video from; the output ratio follows it, '
			'so --ratio is ignored when this is given')
	args = ap.parse_args()

	if not BASE_URL:
		raise SystemExit('genvideo: CLAUDE_BASE_URL is not set')

	key = os.environ.get('PAIGOD_API_KEY')
	if not key:
		raise SystemExit('genvideo: PAIGOD_API_KEY is not set')

	if args.task:
		# With --task there is only one useful positional, the output path, but
		# argparse binds the first positional to prompt_file. Without this shift,
		# `--task ID out.mp4` silently printed the URL instead of downloading,
		# because `out` stayed empty.
		if args.prompt_file and not args.out:
			args.out, args.prompt_file = args.prompt_file, None

		body = status(args.task, key)
		state = body.get('status', '?')
		if state not in TERMINAL:
			print('task %s is %s' % (args.task, state), file=sys.stderr)
			body = wait(args.task, key)
		return finish(body, args.out, args.task)

	if not args.prompt_file:
		ap.error('a prompt file is required unless --task is given')

	if args.duration != -1 and not (DURATION_RANGE[0] <= args.duration <= DURATION_RANGE[1]):
		raise SystemExit('genvideo: duration must be -1 or between %d and %d' % DURATION_RANGE)

	text = sys.stdin.read() if args.prompt_file == '-' else open(args.prompt_file, encoding='utf-8').read()
	prompt = text.strip()
	if not prompt:
		raise SystemExit('genvideo: prompt is empty')

	if args.first_frame and not os.path.isfile(args.first_frame):
		raise SystemExit('genvideo: no such first frame: %s' % args.first_frame)

	shape = 'from %s' % args.first_frame if args.first_frame else args.ratio
	print('creating a %ds %s %s task, %d chars of prompt (this bills and cannot be cancelled)'
		% (args.duration, shape, args.resolution, len(prompt)), file=sys.stderr)

	task = create(prompt, key, args.duration, args.ratio, args.resolution, args.audio,
		args.first_frame)
	print('  task %s' % task, file=sys.stderr)

	body = wait(task, key)

	return finish(body, args.out, task)


if __name__ == '__main__':
	sys.exit(main())
