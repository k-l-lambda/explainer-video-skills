"""Synthesize speech from a saved voice_clone_prompt.pt (Qwen3-TTS Base).

    python synthesize.py voices/<voice-id>/voice_clone_prompt.pt '<text>' --model <model-dir> --out line.wav
"""
import argparse, json, time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel
from qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem

parser = argparse.ArgumentParser()
parser.add_argument('prompt', type=Path, help='voice_clone_prompt.pt from extract_prompt.py')
parser.add_argument('text')
parser.add_argument('--language', default='Chinese')
parser.add_argument('--mode', choices=['icl', 'xvec'], default='icl')
parser.add_argument('--model', default='.local/models/qwen3-tts-base')
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()

saved = torch.load(args.prompt)
icl = args.mode == 'icl'
# Pass a list of items, not a dict: only the list path tokenizes ref_text for ICL.
item = VoiceClonePromptItem(ref_code=saved['ref_code'] if icl else None,
                            ref_spk_embedding=saved['ref_spk_embedding'],
                            x_vector_only_mode=not icl, icl_mode=icl,
                            ref_text=saved['ref_text'] if icl else None)
model = Qwen3TTSModel.from_pretrained(args.model, device_map='cuda', dtype=torch.bfloat16,
                                      attn_implementation='sdpa')
torch.manual_seed(args.seed); np.random.seed(args.seed)
started = time.monotonic()
wavs, sr = model.generate_voice_clone(text=args.text, language=args.language,
                                      voice_clone_prompt=[item], max_new_tokens=1024)
wall = time.monotonic()-started
wav = np.asarray(wavs[0], dtype=np.float32)
sf.write(args.out, wav, sr, subtype='FLOAT')
# Speaker similarity of the output against the reference embedding.
import librosa
w24 = librosa.resample(wav, orig_sr=sr, target_sr=24000) if sr != 24000 else wav
emb = model.model.extract_speaker_embedding(w24.astype(np.float32), 24000).float().cpu()
cos = float(torch.nn.functional.cosine_similarity(emb, saved['ref_spk_embedding'].float(), dim=0))
print(json.dumps(dict(out=str(args.out), mode=args.mode, seconds=len(wav)/sr, sr=sr,
                      wall_seconds=round(wall, 1), cosine_to_reference=round(cos, 4)), ensure_ascii=False))
