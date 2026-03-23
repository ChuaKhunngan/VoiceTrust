# VoiceTrust Runtime

Self-contained runtime for the `Skill-VoiceTrust` bundle.

## Included
- local SpeechBrain ECAPA speaker-verification assets under `assets/models/`
- runtime source under `src/`
- runtime config under `configs/`
- owner profile storage under `data/owners/`

## First-time setup
Before setup, prepare **3 to 5** audio samples from the intended owner.
All samples should be from the same person and should use clean, natural speech.

From this `runtime/` directory:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
uv run --python .venv/bin/python ../scripts/demo.py --list-speakers
```

## Enroll owner samples
```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_01.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

## Normal verification
```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```
