---
name: tts
description: Synthesize narration in a cloned voice with Qwen3-TTS 1.7B Base, locally. Use when asked to generate TTS / narration / a voice line from a reference voice or a saved voice embedding, to build a voice-clone prompt from a reference clip plus its transcript, or to voice an explainer's script before the edit.
---

# TTS with a cloned voice (Qwen3-TTS Base)

**Machine-specific values** go in `doc.local.md` in this skill's folder (ignored by git through `*.local.*`). It gives the values for the placeholders below:

- `<python>`: the venv's Python, or a wrapper that sets its environment;
- `<model-dir>`;
- `<voices>`;
- the proxy and the GPU;
- the voices that already exist.

If it is missing, ask the user where the model and the venv are, and write it.

The scripts are in this skill's `scripts/` folder: `extract_prompt.py` and `synthesize.py`.

## Requirements

- **Model**: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, in `<model-dir>`.
  - Only **Base** models can clone: VoiceDesign (text description) and CustomVoice (preset speakers) raise on `generate_voice_clone`.
  - The speaker encoder is inside the Base checkpoint: an ECAPA-TDNN, 2048-d for 1.7B. No separate embedding model is needed.
- **Python packages**: `qwen-tts==0.1.1` (upstream: https://github.com/QwenLM/Qwen3-TTS), `librosa`, `soundfile`.
  - `sox` must be on `PATH`. Without it the import prints "SoX could not be found!" and fails.
- **Hardware**: a CUDA GPU. On an RTX 3090, a sentence takes about 14–16 s including the model load.
- **Download** if the model is missing (about 4.3 GB). This works whether or not the `hf` / `huggingface-cli` command is installed:
  `<python> -c "from huggingface_hub import snapshot_download as d; d('Qwen/Qwen3-TTS-12Hz-1.7B-Base', local_dir='<model-dir>')"`
  - Set `HF_ENDPOINT=https://hf-mirror.com` where huggingface.co is slow.
  - `HF_HUB_DISABLE_XET=1` avoids the Xet transfer backend when it stalls.

## 1. Build a voice-clone prompt (once per voice)

Input: a clean reference clip (a few seconds to about 30 s) and its **exact** transcript, as SRT or as `--ref-text`.

```bash
<python> <skill>/scripts/extract_prompt.py <ref.wav> <ref.srt> --model <model-dir> --out <voices>/<voice-id>
<python> <skill>/scripts/extract_prompt.py <ref.wav> --ref-text '<exact transcript>' --model <model-dir> --out <voices>/<voice-id>
```

- **Transcript joining**: the script joins the SRT cue texts without separators into `ref_text`. That suits Chinese; for languages with spaces, pass `--ref-text` instead.
- **Call**: `create_voice_clone_prompt(ref_audio=(wav, sr), ref_text, x_vector_only_mode=False)` in float32.
- **Outputs**:
  - `voice_clone_prompt.pt`: `ref_code` [frames, 16] at about 12.5 frames/s, `ref_spk_embedding` (2048-d), `ref_text` and the mode flags;
  - `speaker_embedding.npy`;
  - `report.json`, with a half-vs-half cosine check. About 0.99 means the voice is consistent.

## 2. Synthesize

```bash
<python> <skill>/scripts/synthesize.py <voices>/<voice-id>/voice_clone_prompt.pt '<text>' \
  --model <model-dir> --language Chinese --mode icl --out <out.wav> [--seed 42]
```

- `--mode icl` (default, better quality): conditions on the reference codes, `ref_text` and the embedding. The reference part is decoded together with the new text and then cut off, so the output contains only the new text.
- `--mode xvec`: uses only the 2048-d speaker embedding, with no codes and no transcript. Quality may be lower.
- Output is a 24 kHz float WAV. The script prints JSON with `seconds`, `wall_seconds` and `cosine_to_reference`.
- `--language`: Chinese, English, … The API also accepts `Auto`.

## Narrating an explainer

Synthesize one file per scene (or per sentence, then concatenate), named after the scene. Then hand them to the edit:

1. **Captions**: `scripts/transcribe-captions.py` (repo root) turns each file into word-timed captions.
2. **Scene lengths**: `scripts/sync-scene.mjs` sets each Remotion scene's length to its audio and writes the captions in.

See **explainer-video** `references/studio-editable.md`. Keep the narration script's text as the source of truth for caption wording: compare it with the transcript and fix homophones.

## Using the API directly

```python
import torch
from qwen_tts import Qwen3TTSModel
from qwen_tts.inference.qwen3_tts_model import VoiceClonePromptItem

saved = torch.load('voice_clone_prompt.pt')
item = VoiceClonePromptItem(ref_code=saved['ref_code'], ref_spk_embedding=saved['ref_spk_embedding'],
                            x_vector_only_mode=False, icl_mode=True, ref_text=saved['ref_text'])
# x-vector only: ref_code=None, ref_text=None, x_vector_only_mode=True, icl_mode=False
model = Qwen3TTSModel.from_pretrained('<model-dir>', device_map='cuda',
                                      dtype=torch.bfloat16, attn_implementation='sdpa')
wavs, sr = model.generate_voice_clone(text='…', language='Chinese', voice_clone_prompt=[item],
                                      max_new_tokens=1024)
```

## Pitfalls

- **Pass a list, not a dict**: `voice_clone_prompt` must be a **list** of `VoiceClonePromptItem`. With a dict, `ref_texts_for_ids` becomes `None` and ICL silently loses the tokenized reference transcript.
- **ICL needs `ref_text`**: without it, the call raises `ref_text is required when x_vector_only_mode=False (ICL mode)`.
- **Sampling defaults** come from the Base `generation_config.json`: temperature 0.9 and top_k 50, for both talker and subtalker. Seed torch and numpy for repeatable output; the script uses 42.
- **Long texts**: `max_new_tokens=1024` is about 80 s of audio at 12.5 frames/s. Split longer text into sentences and concatenate the results.
- **Reading speaker cosine**: different speakers still score about 0.92, because the embedding space is anisotropic. The same voice scores about 0.98–0.99.

## Checking a result

- **Intelligibility**: transcribe the output back with faster-whisper (`scripts/transcribe-captions.py`). The base and small models make homophone errors; use a larger model for a real check.
- **Similarity**: compare `cosine_to_reference` against the 0.92 / 0.99 reference points above.

## Ethics

- **Consent and labelling**: clone a real person's voice only with their consent, and label the output as synthetic.
- **Voices taken without consent**: speech made from a voice taken from public media without consent stays a local experiment. Do not publish or share it.
- **Published work**: for a published explainer, use your own voice, a voice you have a licence for, or a synthetic voice.

## Not yet verified

- A listening comparison of ICL vs x-vector.
- Behaviour on long texts.
- Variation across seeds.
- Whether background music in the reference clip leaks into the embedding.
