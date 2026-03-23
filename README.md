# VoiceTrust for OpenClaw

VoiceTrust is a voice-message trust layer for OpenClaw. It is designed to answer a practical question in channel workflows:

> Is this incoming voice message likely to be spoken by the enrolled owner?

The current project direction is integration-first:
- prefer proven open-source speaker verification components
- keep latency practical for real voice-note workflows
- return structured trust signals instead of pretending to be perfect biometric authentication

---

## Current Status

This repository is in early open-source preparation.

The current public-facing mainline is centered on:
- SpeechBrain-based speaker verification
- owner-profile persistence
- audio-quality and speech-activity metadata
- a simple local CLI/demo path

Historical import artifacts and restructuring notes are preserved under `archive/` and are not part of the public mainline story.

---

## Product Goal

VoiceTrust sits on the voice-message path:

1. incoming voice message
2. audio preprocessing
3. speaker verification / trust evaluation
4. structured trust output
5. OpenClaw decides how to use that signal

Primary target question:
- **Is this likely the enrolled owner speaking?**

Non-goals for the first versions:
- perfect standalone biometric authentication
- training custom production models from scratch
- overengineered research architecture before integration is proven

---

## Current Technical Direction

Current mainline direction:
- **Speaker verification:** SpeechBrain ECAPA-TDNN based flow
- **Voiceprint persistence:** owner profile support
- **Trust scoring:** speaker verification + audio quality
- **Speech metadata:** `speech_duration`, `speech_ratio`, `vad_status`, `failure_reason`

Long-term direction:
- keep VoiceTrust independent from STT backend choice
- keep mature OSS components where possible
- keep custom code focused on orchestration, scoring, persistence, and integration
- keep OpenClaw consumption easy and explicit

---

## Repository Layout

```text
voicetrust/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── configs/
├── assets/models/
├── scripts/demo.py
├── src/
├── tests/
├── docs/
└── archive/
```

Public mainline intent:
- `scripts/demo.py` — local CLI/demo entry
- `src/` — runtime logic
- `configs/` — current runtime config
- `assets/models/` — local project-owned model assets
- `tests/` — minimal smoke and owner-profile tests
- `docs/` — public-facing docs
- `archive/` — historical materials not needed for normal runtime

---

## What Comes Next

Expected next steps:
1. tighten public docs and dependency story
2. keep only the minimum supported runtime path in mainline
3. make tests independent from historical import artifacts
4. clarify what is supported vs archived
5. prepare first public release hygiene

See also:
- `docs/quickstart.md`
- `docs/model-assets.md`
- `archive/`
