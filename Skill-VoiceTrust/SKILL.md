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

## Output fields

VoiceTrust results may include:
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

## Trust label rule

Use `overall_trust` as the main label driver and `confidence` as a check.

- **high**: `overall_trust >= 80` and `confidence >= 70` and `failure_reason == null`
- **medium**: `overall_trust >= 60` and `confidence >= 50` and no hard failure
- **low**: everything else

Downgrade one level if:
- `vad_status != "ok"`
- `speech_duration < 2.0`
- `speech_ratio < 0.35`

Never call it `high` if `failure_reason` is non-null.

## Human rendering

Preferred compact rendering:
- `Voice trust: high / medium / low`
- `Details: match <x> · trust <y> · confidence <z> · quality <q>`

If degraded, say why briefly.
Do not over-claim certainty.

## Failure handling

- If STT succeeds and VoiceTrust fails: keep transcript, report trust as unavailable/inconclusive.
- If VoiceTrust succeeds and STT fails: keep trust result, report transcription failure.
- If both fail: say the audio could not be processed reliably.

## First-time setup

For first-time environment setup, local installation, enrollment, or bootstrap instructions, read:
- `references/quickstart.md`

Normal voice-message handling should not need the full quickstart.
