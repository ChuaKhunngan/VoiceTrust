# VoiceTrust Runtime

Self-contained runtime for the `Skill-VoiceTrust` bundle.

## Included
- local SpeechBrain ECAPA speaker-verification assets under `assets/models/`
- runtime source under `src/`
- runtime config under `configs/`
- smoke fixtures under `tests/fixtures/`

## First-time setup
From this `runtime/` directory:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
uv run --python .venv/bin/python ../scripts/demo.py --list-speakers
```

## Normal verification
```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```
