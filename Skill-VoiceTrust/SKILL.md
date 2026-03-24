---
name: voicetrust
description: Interpret VoiceTrust results for owner verification on voice/audio inputs. Use when you need the meaning of VoiceTrust fields, trust labels, concise result rendering, or the minimal rule for handling voice messages alongside STT. For first-time setup or environment bootstrap, read `references/quickstart.md`.
---

# VoiceTrust

VoiceTrust is the trust side of voice handling.
It answers: is this audio likely spoken by the enrolled owner?

Normal use:
- when voice arrives, run **STT** for content
- run **VoiceTrust** for speaker trust
- merge both into one response

Do not use this skill to define machine-specific commands.
Local commands and local routing belong elsewhere.

## Runtime packaging note

This ClawHub-friendly skill bundle is intentionally lightweight:
- source code and setup docs are included
- large model checkpoint files are **not** bundled
- enrolled owner data is **local runtime state** and must not be published

If VoiceTrust initialization fails because model assets are missing, read:
- `references/quickstart.md`

## Output fields

VoiceTrust results may include:
- `speaker_match`
- `audio_quality`
- `overall_trust`
- `confidence`
- `identity_score`
- `trust_label`
- `decision`
- `decision_reasons`
- `speaker_id`
- `speech_duration`
- `speech_ratio`
- `vad_status`
- `failure_reason`
- `raw_scores.speaker_similarity`

## Trust and execution rule

Use `trust_label` for concise human rendering.
Use `decision` for command gating.
Do not treat audio quality alone as owner identity evidence.

### Trust label

Use owner-focused scoring:
- **high**: `identity_score >= 85` and `confidence >= 80` and `failure_reason == null`
- **medium**: `identity_score >= 72` and `confidence >= 68` and `failure_reason == null`
- **low**: everything else

Typical downgrade signals:
- `vad_status != "ok"`
- `speech_duration < 2.5`
- `speech_ratio < 0.45`
- `speaker_match < 70`
- `failure_reason != null`

Never call it `high` if `failure_reason` is non-null.

### Executable command gate

For voice command execution:
- normal execution path: `speech_duration >= 3.0`
- short-voice override: allow `speech_duration >= 1.2` only when `speaker_match >= 85` and `confidence >= 85`
- base execution gate still requires all of the following:
  - `speaker_match >= 78`
  - `confidence >= 80`
  - `identity_score >= 82`
  - `vad_status == "ok"`
  - `failure_reason == null`

Interpretation:
- `trust_label = high` does **not** automatically mean command approval
- `decision = "allow_command"` is the authority for whether a voice command may run
- `decision != "allow_command"` means keep transcript handling separate from command execution
- `decision` is for command gating, not for blocking ordinary non-command voice replies
- music / non-speech / non-command audio should not be treated as a voice-command candidate

## Human rendering

Preferred compact rendering:
- `Voice trust: high / medium / low`
- `Details: match <x> · trust <y> · confidence <z> · identity <i> · quality <q>`
- if relevant: `Decision: allow_command / reject_command`

If degraded, say why briefly using `decision_reasons`.
Do not over-claim certainty.

## Failure handling

- If STT succeeds and VoiceTrust fails: keep transcript, report trust as unavailable/inconclusive.
- If VoiceTrust succeeds and STT fails: keep trust result, report transcription failure.
- If both fail: say the audio could not be processed reliably.
- If trust is present but `decision != "allow_command"`: do not execute voice commands; ask for text confirmation or a clearer/longer sample when needed.

## First-time setup

For first-time environment setup, local installation, enrollment, or bootstrap instructions, read:
- `references/quickstart.md`

Normal voice-message handling should not need the full quickstart.
