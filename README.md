# VoiceTrust

VoiceTrust is a lightweight voice-message trust layer for OpenClaw.
It answers one practical question:

> Is this incoming voice message likely to be spoken by the enrolled owner?

Version **0.1.0** is the first public release.
This release focuses on a simple, local, integration-first workflow:

- owner voice enrollment with multiple samples
- speaker verification against an enrolled owner profile
- structured trust output for OpenClaw voice-message handling
- a self-contained `Skill-VoiceTrust/` bundle for skill-style distribution

VoiceTrust is **not** presented as perfect biometric authentication.
It is a practical trust signal for real channel workflows.

---

## What 0.1.0 Includes

- **SpeechBrain ECAPA-based speaker verification**
- **Multi-sample owner profiles**
- **Aggregate owner embedding generation**
- **Structured trust output**, including:
  - `speaker_match`
  - `audio_quality`
  - `overall_trust`
  - `confidence`
  - `speech_duration`
  - `speech_ratio`
  - `vad_status`
  - `failure_reason`
- **Local CLI / demo path** via `scripts/demo.py`
- **Packaged skill bundle** under `Skill-VoiceTrust/`

---

## Repository Layout

```text
VoiceTrust/
├── README.md
├── LICENSE
├── pyproject.toml
├── requirements.txt
├── configs/
├── assets/models/
├── scripts/demo.py
├── src/
├── docs/
├── archive/
└── Skill-VoiceTrust/
```

Main parts:
- `scripts/demo.py` — local CLI/demo entrypoint
- `src/` — core runtime logic
- `configs/` — current runtime config
- `assets/models/` — local model assets used by the project
- `docs/` — project notes and public-facing documentation
- `archive/` — historical materials not needed for normal use
- `Skill-VoiceTrust/` — portable skill bundle for OpenClaw-style use

---

## Quick Start

### 1. Create a local environment

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

### 2. Enroll owner samples

Use **3 to 5** clean voice samples from the same person.

```bash
uv run --python .venv/bin/python scripts/demo.py \
  --audio /path/to/owner_sample_01.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

Repeat with additional owner samples.

### 3. Check enrolled owners

```bash
uv run --python .venv/bin/python scripts/demo.py --list-speakers
```

Expected shape:

```text
Owner profiles:
  - owner
```

### 4. Verify a voice message

```bash
uv run --python .venv/bin/python scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```

---

## Skill Bundle

This repository also includes a bundled OpenClaw-oriented skill package:

- `Skill-VoiceTrust/SKILL.md`
- `Skill-VoiceTrust/references/quickstart.md`
- `Skill-VoiceTrust/scripts/demo.py`
- `Skill-VoiceTrust/runtime/`

Use the skill bundle when you want a portable, self-contained VoiceTrust package
separate from the full project repository.

---

## Intended Usage Pattern

VoiceTrust is designed to sit beside STT, not replace it.

Normal flow:
1. a voice message arrives
2. run STT for transcript/content
3. run VoiceTrust on the same audio
4. merge both before replying or acting

Recommended policy:
- if a message is a **voice command** and trust is too low, do **not** execute the command
- if a message is ordinary conversational audio, low trust does not automatically require discarding the content

---

## Current Limitations

Version 0.1.0 intentionally stays small.

Known limits:
- owner verification is the main supported path
- anti-spoofing is not yet a complete production feature
- the trust score is a practical heuristic, not a formal identity proof
- model assets are currently stored directly in the repository, which is convenient for bootstrap but may be revised in future releases

---

## Documentation

Useful files:
- `Skill-VoiceTrust/references/quickstart.md`
- `docs/open-source-readiness.md`
- `archive/`

---

## License

MIT
