# VoiceTrust Quickstart

This guide is for the **first time** you set up VoiceTrust after downloading the `Skill-VoiceTrust/` package.
It explains how to prepare the runtime, enroll the owner voiceprint, and verify that the skill is ready for normal use.

For normal day-to-day use, you should not need this file.

---

## Package layout

This quickstart assumes you are already inside the `Skill-VoiceTrust/` directory.

Relevant paths in this package:

- `SKILL.md`
- `references/quickstart.md`
- `scripts/demo.py`
- `runtime/`

The actual VoiceTrust runtime lives under `runtime/`.

---

## 1. Enter the runtime directory

From the package root:

```bash
cd runtime
```

All setup commands below are run from inside `runtime/`.

---

## 2. Create the virtual environment

Create a local virtual environment with `uv`:

```bash
uv venv .venv
```

---

## 3. Install dependencies

Install the required Python packages:

```bash
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python torchcodec
```

`torchcodec` is required for the current SpeechBrain audio-loading path.

---

## 4. Verify that the runtime starts

Run a basic speaker listing command:

```bash
./.venv/bin/python ../scripts/demo.py --list-speakers
```

If this is the first setup, it is normal to see that no enrolled speaker exists yet.

---

## 5. Enroll the owner voiceprint

Before VoiceTrust can verify anyone, you must enroll the owner.

Recommended policy:
- record **3 to 5** short owner voice samples
- use clean speech when possible
- prefer natural speaking voice
- avoid heavy background noise
- prefer clips in the rough **3–10 second** range

For each sample, run:

```bash
./.venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_01.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

Then repeat with additional files:

```bash
./.venv/bin/python ../scripts/demo.py \
  --audio /path/to/owner_sample_02.wav \
  --speaker owner \
  --enroll-sample \
  --json

./.venv/bin/python ../scripts/demo.py \
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

---

## 6. Confirm enrollment state

After enrollment, confirm that the owner profile exists:

```bash
./.venv/bin/python ../scripts/demo.py --list-speakers
```

Expected shape:

```text
Owner profiles:
  - owner
```

---

## 7. Run a verification test

Pick a voice sample that should match the enrolled owner and run:

```bash
./.venv/bin/python ../scripts/demo.py \
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

## 8. Register the local voice-message convention in `TOOLS.md`

After VoiceTrust is working, add a local convention to your `TOOLS.md`.

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

## 9. Understand the current trust rule

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

## 10. How to use VoiceTrust in normal operation

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
./.venv/bin/python ../scripts/demo.py \
  --audio /path/to/incoming_audio.ogg \
  --speaker owner \
  --json
```

---

## 11. Recommended operational habits

- keep using the same `speaker_id` for the same owner
- prefer a small curated owner sample set over random noisy clips
- if recognition drifts, re-enroll with better samples instead of blindly adding many bad ones
- do not treat VoiceTrust as perfect biometric authentication
- treat the result as a trust signal, not as the sole high-risk security factor

---

## 12. When to revisit this quickstart

Read this file again when:
- setting up the package on a new machine
- rebuilding the environment
- re-enrolling the owner profile
- fixing a broken runtime

For normal incoming voice handling, you should usually only need:
- `SKILL.md`
- your local voice-message handling convention
