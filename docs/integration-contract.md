# Integration Contract (Draft)

## Purpose

This document defines the intended integration boundary between OpenClaw and VoiceTrust.

VoiceTrust is an **audio trust layer**. It does not assume any specific STT backend.

---

## Contract philosophy

OpenClaw may use any STT strategy before, after, or independently from VoiceTrust.
VoiceTrust should accept audio as audio, and return trust information as structured data.

---

## Input

### Required
- `audio_path`: path to the prepared audio artifact

### Optional
- `speaker_id`: target enrolled owner id (initial MVP default: `owner`)
- `expected_language`: optional expectation hint
- `context`: optional metadata from caller, not required for core trust path

### Important
VoiceTrust should not require:
- transcript text
- ASR confidence
- any specific cloud ASR provider

---

## Output

Structured result should include at least:
- `speaker_match`
- `overall_trust`
- `confidence`
- `audio_quality`
- `spoof_probability`
- `is_synthetic`
- `speaker_id`

Planned metadata additions for upcoming phases:
- `speech_duration`
- `speech_ratio`
- `vad_status`
- `detected_language`
- `language_confidence`
- `failure_reason`

Current local mainline already emits early versions of:
- `speech_duration`
- `speech_ratio`
- `vad_status`
- `failure_reason`

---

## Failure / uncertainty states

Planned first-class states:
- `no_owner_enrolled`
- `audio_not_found`
- `insufficient_speech`
- `too_short`
- `too_noisy`
- `verification_unavailable`
- `spoof_backend_unavailable`
- `language_id_unavailable`
- `inconclusive`

These should be exposed explicitly instead of being hidden inside vague low scores.

---

## STT independence rule

VoiceTrust must remain independent from downstream STT strategy.

Examples:
- OpenClaw may run VoiceTrust before transcription
- OpenClaw may transcribe first and run VoiceTrust second
- OpenClaw may skip transcription entirely and only use VoiceTrust

None of these should require a code-path rewrite inside VoiceTrust.

---

## MVP evaluation path

### Current mainline
- audio input
- speaker verification
- quality analysis
- trust aggregation

### Planned near-term additions
- VAD / segmentation
- language-aware metadata
- improved owner enrollment handling

---

## Non-goals

VoiceTrust is not intended to be:
- the only high-risk authentication factor
- a hard dependency of STT
- a transcript-semantic reasoning engine
- a replacement for channel policy logic in OpenClaw
