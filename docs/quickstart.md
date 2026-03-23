# Quick Start

VoiceTrust is a local, STT-independent audio trust layer focused on:
- speaker verification
- audio quality
- speech activity metadata

Current mainline engine:
- SpeechBrain 1.0.3
- local project-owned ECAPA model assets under `assets/models/ecapa_voxceleb/`

---

## 1. Enter the project

```bash
cd /path/to/voicetrust
```

## 2. Create or activate the environment

If needed, create a local environment:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

Then use the project-local interpreter:

```bash
./.venv/bin/python --version
```

---

## 3. Check enrollment state

```bash
./.venv/bin/python scripts/demo.py --list-speakers
```

Expected output shape:

```text
Owner profiles:
  - owner
```

---

## 4. Append a new owner sample

Recommended enrollment flow:

```bash
./.venv/bin/python scripts/demo.py \
  --audio /path/to/your_audio.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

This updates owner-profile files under `data/owners/`.

---

## 5. Verify an audio sample

```bash
./.venv/bin/python scripts/demo.py \
  --audio /path/to/test_audio.wav \
  --speaker owner \
  --json
```

Current output fields:
- `speaker_match`
- `audio_quality`
- `overall_trust`
- `confidence`
- `speaker_id`
- `speech_duration`
- `speech_ratio`
- `vad_status`
- `failure_reason`
- `raw_scores.speaker_similarity`

---

## 6. Current trust formula

```text
overall_trust = 0.75 * speaker_match + 0.25 * audio_quality
```

This is the current no-anti-spoofing mainline.

---

## 7. Run minimal tests

```bash
./.venv/bin/python -m pytest tests/test_smoke.py tests/test_owner_profiles.py -q
```

Expected result:

```text
2 passed
```

---

## Notes

### Current mainline scope
VoiceTrust currently focuses on:
- speaker verification
- audio quality
- VAD-style metadata

### Not currently in final output
The following are intentionally not part of the current final output because they are not fully implemented as production-meaningful signals:
- anti-spoofing
- language ID

### Model assets
The local speaker model assets live at:

```text
assets/models/ecapa_voxceleb/
```

VoiceTrust does not rely on Hugging Face at runtime for the main speaker path.
