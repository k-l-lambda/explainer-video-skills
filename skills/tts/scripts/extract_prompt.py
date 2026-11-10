"""Build a reusable Qwen3-TTS voice-clone prompt (speaker embedding + ICL codes) from audio + SRT or text.

    python extract_prompt.py ref.wav ref.srt --model <model-dir> --out voices/<voice-id>
"""
import argparse, json, re
from pathlib import Path

import librosa
import numpy as np
import torch
from qwen_tts import Qwen3TTSModel

parser = argparse.ArgumentParser()
parser.add_argument('audio')
parser.add_argument('srt', nargs='?', help='SRT transcript; or use --ref-text')
parser.add_argument('--ref-text', help='Exact transcript, instead of an SRT')
parser.add_argument('--model', default='.local/models/qwen3-tts-base')
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()

# SRT cue text in order; Chinese cues join without separators.
if (args.srt is None) == (args.ref_text is None):
    parser.error('give exactly one of SRT or --ref-text')
if args.ref_text is not None:
    ref_text = args.ref_text
else:
    blocks = re.split(r'\n\s*\n', Path(args.srt).read_text(encoding='utf-8').strip())
    ref_text = ''.join(' '.join(b.splitlines()[2:]).strip() for b in blocks)

wav, sr = librosa.load(args.audio, sr=None, mono=True)
model = Qwen3TTSModel.from_pretrained(args.model, device_map='cuda', dtype=torch.float32,
                                      attn_implementation='sdpa')
item = model.create_voice_clone_prompt(ref_audio=(wav, sr), ref_text=ref_text,
                                       x_vector_only_mode=False)[0]

# Consistency check: embeddings of the two halves should be close to the full clip.
emb = item.ref_spk_embedding.float().cpu()
w24 = librosa.resample(wav, orig_sr=sr, target_sr=24000)
half = len(w24)//2
parts = [model.model.extract_speaker_embedding(w24[i:i+half].astype(np.float32), 24000).float().cpu()
         for i in (0, half)]
cos = lambda a, b: float(torch.nn.functional.cosine_similarity(a, b, dim=0))

args.out.mkdir(parents=True, exist_ok=True)
torch.save(dict(ref_code=item.ref_code.cpu(), ref_spk_embedding=emb, ref_text=ref_text,
                x_vector_only_mode=False, icl_mode=True), args.out/'voice_clone_prompt.pt')
np.save(args.out/'speaker_embedding.npy', emb.numpy())
report = dict(audio=str(Path(args.audio).resolve()), srt=str(Path(args.srt).resolve()) if args.srt else None,
              model=args.model,
              source=json.loads(Path(args.model, 'source.json').read_text()) if Path(args.model, 'source.json').exists() else None,
              seconds=len(wav)/sr, ref_text=ref_text, ref_text_chars=len(ref_text),
              embedding_dim=emb.numel(), embedding_norm=float(emb.norm()),
              ref_code_shape=list(item.ref_code.shape),
              cosine_full_vs_first_half=cos(emb, parts[0]), cosine_full_vs_second_half=cos(emb, parts[1]),
              cosine_first_vs_second_half=cos(parts[0], parts[1]))
(args.out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps(report, ensure_ascii=False, indent=2))
