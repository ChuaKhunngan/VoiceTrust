# VoiceTrust Quickstart

This guide is for the **first time** you set up VoiceTrust after downloading the `Skill-VoiceTrust/` package.
It explains how to register the local usage convention, prepare the runtime, collect the owner audio, prepare the local model assets, enroll the owner voiceprint, and verify that the skill is ready for normal use.

For normal day-to-day use, you should not need this file.

---

## Package layout

This quickstart assumes you are already inside the `Skill-VoiceTrust/` directory.

Relevant paths in this package:

- `SKILL.md`
- `references/quickstart.md`
- `scripts/demo.py`
- `scripts/ensure_models.py`
- `runtime/`

The actual VoiceTrust runtime lives under `runtime/`.
The publishable skill bundle intentionally stays lightweight:
- source code and setup docs are included
- large SpeechBrain checkpoint files are **not** bundled into the ClawHub package
- owner enrollment data is **local-only** and should never be distributed

---

## 1. Register the local voice-message convention in `TOOLS.md`

Before you do runtime setup, register the local voice-handling rule in your `TOOLS.md`.
This makes the intended day-to-day behavior explicit before enrollment and verification work begin.

The intended rule is:
- when a voice message arrives, do **STT**
- also run **VoiceTrust**
- merge both before replying
- if the message is a **voice command** and VoiceTrust confidence is too low, **do not execute the command**
- if the message is **not** being treated as a command (for example: chat content, narration, music, or other non-command audio), it may still be handled as ordinary content

Recommended wording:

```md
## Incoming Voice Message
- Do STT.
- Also run VoiceTrust.
- Merge both before replying.
- If this is a voice command and trust is low, do not execute the command.
- If this is not a command, low trust does not automatically block normal content handling.
```

Keep this section short.
Do not put machine-specific paths into the skill itself.
Put local behavior conventions in `TOOLS.md`.

---

## 2. Collect the owner audio first

Before you initialize VoiceTrust for real use, you must decide **whose voice** will be treated as the owner.
VoiceTrust is not useful until the owner voiceprint is enrolled.

Required preparation:
- choose the owner identity first
- prepare **3 to 5** owner voice samples before enrollment
- keep all samples from the **same person**
- prefer natural speech in the owner’s usual speaking voice
- avoid heavy background noise, music, or overlapping speakers
- prefer clips in the rough **3–10 second** range

Recommended naming example:

```text
/path/to/owner_sample_01.wav
/path/to/owner_sample_02.wav
/path/to/owner_sample_03.wav
```

Recommended `speaker_id`:
- `owner`

If you do not have the owner audio yet, stop here and gather it first.

---

## 3. Enter the runtime directory

From the package root:

```bash
cd runtime
```

All setup commands below are run from inside `runtime/`.

---

## 4. Create the virtual environment

Create a local virtual environment with `uv`:

```bash
uv venv .venv
```

---

## 5. Install dependencies

Install the required Python packages:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

`torchcodec` is required for the current SpeechBrain audio-loading path.

---

## 6. Prepare the local model assets

The ClawHub package does **not** include the large SpeechBrain checkpoint files.
Before enrollment or verification, run:

```bash
uv run --python .venv/bin/python ../scripts/ensure_models.py
```

By default, `ensure_models.py` will:
- check whether required local files already exist
- download any missing files from:

```text
https://raw.githubusercontent.com/ChuaKhunngan/VoiceTrust/main/assets/models/ecapa_voxceleb/
```

Expected model directory:

```text
runtime/assets/models/ecapa_voxceleb/
```

Required files:
- `hyperparams.yaml`
- `classifier.ckpt`
- `embedding_model.ckpt`
- `label_encoder.ckpt`
- `mean_var_norm_emb.ckpt`

Useful variants:

```bash
# only inspect status; do not download
uv run --python .venv/bin/python ../scripts/ensure_models.py --check-only

# machine-readable output
uv run --python .venv/bin/python ../scripts/ensure_models.py --json

# force re-download all required files
uv run --python .venv/bin/python ../scripts/ensure_models.py --force
```

---

## 7. Verify that the runtime starts

Run a basic speaker listing command:

```bash
uv run --python .venv/bin/python ../scripts/demo.py --list-speakers
```

If this is the first setup, it is normal to see that no enrolled speaker exists yet.

---

## 8. Enroll the owner voiceprint

Once the owner audio is ready, enroll it under a single `speaker_id`.

For the first sample:

```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_01.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

Then repeat with additional files:

```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_02.wav \
  --speaker owner \
  --enroll-sample \
  --json

uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_03.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

Recommended minimum:
- **3 samples**

Recommended comfortable baseline:
- **5 samples**

This will create owner-profile data under:

```text
data/owners/owner/
```

This data is local runtime state.
Do not publish it.

---

## 9. Confirm enrollment state

After enrollment, confirm that the owner profile exists:

```bash
uv run --python .venv/bin/python ../scripts/demo.py --list-speakers
```

Expected shape:

```text
Owner profiles:
  - owner
```

---

## 10. Run a real verification test

Pick a voice sample that should match the enrolled owner and run:

```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/test_audio.wav \
  --speaker owner \
  --json
```

Expected output fields include:
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

At this stage, the important thing is that:
- the command runs successfully
- a JSON object is returned
- the result looks reasonable for a matching owner sample

---

## 11. Understand the current trust rule

Current mainline formula:

```text
overall_trust = 0.75 * speaker_match + 0.25 * audio_quality
```

Current label guidance:
- **high**: `overall_trust >= 80` and `confidence >= 70` and `failure_reason == null`
- **medium**: `overall_trust >= 60` and `confidence >= 50` and no hard failure
- **low**: everything else

Practical downgrades:
- downgrade one level if `vad_status != "ok"`
- downgrade one level if `speech_duration < 2.0`
- downgrade one level if `speech_ratio < 0.35`

---

## 12. How to use VoiceTrust in normal operation

Once setup is complete, the normal pattern is simple:

1. a voice message arrives
2. run **STT** to get the content
3. run **VoiceTrust** on the same audio file
4. merge both results before replying

VoiceTrust is the trust side of the workflow.
It does **not** replace STT.

Typical VoiceTrust command shape during normal use:

```bash
cd runtime
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```

```text
Owner profiles:
  - owner
```

---

## 10. Run a real verification test

Pick a voice sample that should match the enrolled owner and run:

```bash
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/test_audio.wav \
  --speaker owner \
  --json
```

Expected output fields include:
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

At this stage, the important thing is that:
- the command runs successfully
- a JSON object is returned
- the result looks reasonable for a matching owner sample

---

## 11. Understand the current trust rule

Current mainline formula:

```text
overall_trust = 0.75 * speaker_match + 0.25 * audio_quality
```

Current label guidance:
- **high**: `overall_trust >= 80` and `confidence >= 70` and `failure_reason == null`
- **medium**: `overall_trust >= 60` and `confidence >= 50` and no hard failure
- **low**: everything else

Practical downgrades:
- downgrade one level if `vad_status != "ok"`
- downgrade one level if `speech_duration < 2.0`
- downgrade one level if `speech_ratio < 0.35`

---

## 12. How to use VoiceTrust in normal operation

Once setup is complete, the normal pattern is simple:

1. a voice message arrives
2. run **STT** to get the content
3. run **VoiceTrust** on the same audio file
4. merge both results before replying

VoiceTrust is the trust side of the workflow.
It does **not** replace STT.

Typical VoiceTrust command shape during normal use:

```bash
cd runtime
uv run --python .venv/bin/python ../scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```

---

## 12. Recommended operational habits

- keep using the same `speaker_id` for the same owner
- prefer a small curated owner sample set over random noisy clips
- if recognition drifts, re-enroll with better samples instead of blindly adding many bad ones
- do not treat VoiceTrust as perfect biometric authentication
- treat the result as a trust signal, not as the sole high-risk security factor

---

## 13. When to revisit this quickstart

Read this file again when:
- setting up the package on a new machine
- rebuilding the environment
- re-enrolling the owner profile
- fixing a broken runtime

For normal incoming voice handling, you should usually only need:
- `SKILL.md`
- your local voice-message handling convention
