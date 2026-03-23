# Local Run Notes

## Status

Local promoted mainline has been smoke-tested successfully under `projects/voicetrust/`.

Validated path:
1. create project-local uv virtualenv
2. install dependencies
3. enroll a local test speaker
4. verify the same audio
5. receive structured JSON output

## Environment

Project-local virtualenv:
- `.venv/`

Created with:
```bash
cd projects/voicetrust
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

## Important compatibility notes

### 1) Local model assets instead of Hugging Face runtime dependency
Current mainline speaker verification uses project-local assets under:
- `assets/models/ecapa_voxceleb/`

VoiceTrust no longer treats Hugging Face as a required runtime dependency for the main speaker path.

### 2) TorchAudio / SpeechBrain compatibility shim
A minimal shim was added in:
- `src/models/speechbrain_wrapper.py`

Reason:
- current torchaudio build no longer exposes `list_audio_backends()`
- current SpeechBrain still expects that symbol during backend checks

This shim is intentionally minimal and should be revisited later if upstream compatibility improves.

### 3) TorchCodec requirement
Speaker enrollment/loading required:
- `torchcodec`

Without it, the current SpeechBrain audio loading path failed at runtime.

## Smoke commands

### Enroll
```bash
cd projects/voicetrust
./.venv/bin/python scripts/demo.py \
  --audio remote-import/snapshot_20260322/test_audio.wav \
  --speaker smoke_owner \
  --enroll \
  --json
```

### Verify
```bash
cd projects/voicetrust
./.venv/bin/python scripts/demo.py \
  --audio remote-import/snapshot_20260322/test_audio.wav \
  --speaker smoke_owner \
  --json
```

## Observed result

Verified local JSON output included:
- `speaker_match` ≈ 100
- `overall_trust` ≈ 70
- `confidence` ≈ 57

## Known remaining issue

Anti-spoofing models are still not available in this local run path.
The current runtime falls back to heuristic / neutral spoof scoring.
This does **not** block speaker-enrollment / verification MVP, but it does block treating spoof detection as production-ready.
