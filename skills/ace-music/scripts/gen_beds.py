"""Several music cues (e.g. one background bed per chapter) from one spec, loading the models once.

    <ace-python> gen_beds.py --ace <ace-repo> --spec beds.json --out <dir> [--only S2,S5] [--force]

The spec (see example-beds.json):

    {"defaults": {"seeds": [11, 23], "timesig": "4", "lm": "acestep-5Hz-lm-1.7B", "dit": "acestep-v15-turbo",
                  "caption_suffix": "Instrumental background score for narration ..."},
     "cues": [{"name": "S0", "caption": "...", "bpm": 66, "key": "D Major", "duration": 120}, ...]}

Per cue: <out>/<name>/<name>-seed<N>.wav (peak -1 dBFS, as ACE-Step writes it) and run.json. A cue whose
run.json exists is skipped unless --force, so an interrupted batch resumes. `caption_suffix` is appended
to every caption (keep the total under 512 characters).
"""
import argparse, json, os, sys, time

ap = argparse.ArgumentParser()
ap.add_argument('--ace', required=True)
ap.add_argument('--spec', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--only', default='', help='comma-separated cue names')
ap.add_argument('--force', action='store_true')
ap.add_argument('--no-think', action='store_true')
a = ap.parse_args()

spec = json.load(open(a.spec, encoding='utf-8'))
d = spec.get('defaults', {})
only = set(filter(None, a.only.split(',')))
cues = [c for c in spec['cues'] if not only or c['name'] in only]
todo = [c for c in cues if a.force or not os.path.exists(os.path.join(a.out, c['name'], 'run.json'))]
if not todo: sys.exit('nothing to do (all cues have run.json; --force to redo)')

ace = os.path.abspath(a.ace)
sys.path.insert(0, ace)
os.environ.setdefault('HF_HUB_OFFLINE', '1')
import torch
import acestep.llm_inference as _li
_Auto = _li.AutoModelForCausalLM
class _AutoBF16:   # load the LM as BF16, not FP32-then-cast (see generate.py)
    @staticmethod
    def from_pretrained(*args, **kw):
        if 'torch_dtype' not in kw and 'dtype' not in kw: kw['torch_dtype'] = torch.bfloat16
        return _Auto.from_pretrained(*args, **kw)
_li.AutoModelForCausalLM = _AutoBF16
from acestep.handler import AceStepHandler
from acestep.llm_inference import LLMHandler
from acestep.inference import GenerationParams, GenerationConfig, generate_music

t0 = time.time()
dit = AceStepHandler()
msg, ok = dit.initialize_service(project_root=ace, config_path=d.get('dit', 'acestep-v15-turbo'), device='cuda')
if not ok: sys.exit(f'DiT init failed: {msg}')
think = not a.no_think and d.get('think', True)
llm = None
if think:
    llm = LLMHandler()
    msg, ok = llm.initialize(checkpoint_dir=os.path.join(ace, 'checkpoints'),
                             lm_model_path=d.get('lm', 'acestep-5Hz-lm-1.7B'), backend='pt', device='cuda')
    if not ok: sys.exit(f'LM init failed: {msg}')
print(f'loaded in {time.time() - t0:.0f} s', flush=True)

for c in todo:
    get = lambda k, dv=None: c.get(k, d.get(k, dv))
    caption = (c['caption'].strip() + ' ' + d.get('caption_suffix', '')).strip()
    if len(caption) > 512: print(f"warning: {c['name']} caption is {len(caption)} chars (>512)", flush=True)
    seeds = [int(s) for s in get('seeds', [11, 23])]
    out = os.path.join(a.out, c['name'])
    os.makedirs(out, exist_ok=True)
    t1 = time.time()
    params = GenerationParams(
        caption=caption, lyrics='[Instrumental]', instrumental=True, bpm=get('bpm'), keyscale=get('key', ''),
        timesignature=str(get('timesig', '')), duration=float(get('duration', -1)),
        inference_steps=int(get('steps', 8)), shift=float(get('shift', 3.0)), thinking=think)
    cfg = GenerationConfig(batch_size=len(seeds), use_random_seed=False, seeds=seeds, audio_format='wav')
    res = generate_music(dit, llm, params, cfg, save_dir=out)
    if not res.success:
        print(f"{c['name']}: generation failed: {res.error}", flush=True); continue
    files = []
    for au, seed in zip(res.audios, seeds):
        seed = au.get('params', {}).get('seed', seed)
        dst = os.path.join(out, f"{c['name']}-seed{seed}.wav")
        os.replace(au['path'], dst)
        files.append({'seed': seed, 'path': dst})
    info = {'name': c['name'], 'caption': caption, 'bpm': get('bpm'), 'key': get('key', ''),
            'timesig': get('timesig', ''), 'duration': get('duration', -1), 'think': think,
            'gen_s': round(time.time() - t1, 1), 'files': files}
    json.dump(info, open(os.path.join(out, 'run.json'), 'w'), ensure_ascii=False, indent=1)
    print(f"{c['name']}: {len(files)} takes in {info['gen_s']} s", flush=True)
