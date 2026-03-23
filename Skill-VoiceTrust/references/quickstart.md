# VoiceTrust Quickstart

Use this document only for first-time setup, bootstrap, or environment repair.
Normal day-to-day voice handling should not need this file.

## Purpose

This quickstart explains how to prepare a machine so the VoiceTrust skill can be used in practice.
It is intentionally separated from `SKILL.md` so the skill stays short.

## What must exist

Before first use, ensure all of the following are prepared:

1. A working VoiceTrust runtime checkout
2. A runnable Python environment for VoiceTrust
3. Required model/runtime dependencies installed
4. An enrolled owner profile
5. A known local command that can run VoiceTrust against an audio file
6. A local STT path configured separately for voice-message handling

## Minimum bootstrap checklist

### 1) Project location
Use your local VoiceTrust runtime directory.
Example:

```bash
cd /path/to/voicetrust
```

### 2) Environment
Typical local environment shape:
- project-local virtualenv at `.venv/`

Typical setup pattern:
```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

### 3) Owner enrollment
Ensure an owner profile exists before expecting meaningful verification.
Typical command shape:
```bash
./.venv/bin/python scripts/demo.py \
  --audio /path/to/owner_sample.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

### 4) Smoke test
Verify the setup with a known audio sample:
```bash
./.venv/bin/python scripts/demo.py \
  --audio /path/to/test_audio.wav \
  --speaker owner \
  --json
```

Expected output should include fields such as:
- `speaker_match`
- `overall_trust`
- `confidence`
- `vad_status`
- `failure_reason`

### 5) Local protocol registration
After the local VoiceTrust command is confirmed, register the machine-specific voice-message handling convention in `TOOLS.md`.
That file is where local command paths and incoming-voice handling rules belong.

## When to read this file

Read this file when:
- setting up VoiceTrust on a machine for the first time
- rebuilding the environment
- repairing a broken VoiceTrust runtime
- re-enrolling the owner profile

Do not read this file for routine incoming voice-message handling unless setup is broken.
