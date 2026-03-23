# Upstream Policy

## Primary upstream

VoiceTrust uses **SpeechBrain 1.0.3** as its primary speech engine upstream.

Current policy:
- pin upstream package version to `speechbrain==1.0.3`
- build VoiceTrust as a thin, explicit trust layer on top of upstream capabilities
- avoid copying or re-implementing SpeechBrain internals unless absolutely necessary
- keep local compatibility work inside VoiceTrust wrappers, not by forking upstream prematurely

## Why pin 1.0.3

Reasons for pinning:
- reproducible local development
- reproducible open-source onboarding
- stable API target for wrappers and tests
- easier documentation and issue triage

## What belongs upstream vs local

### Upstream responsibility
- speech model implementations
- pretrained inference interfaces
- core speech-task toolkit behavior

### VoiceTrust responsibility
- owner verification workflow
- trust scoring and decision metadata
- VAD / language-aware integration choices
- failure-state semantics
- OpenClaw-facing interface
- STT-independent audio trust contract

## Upgrade policy

Future upgrades beyond 1.0.3 should be deliberate and gated by:
- passing local smoke tests
- no regression in owner vs non-owner separation
- wrapper compatibility review
- changelog / release note review where available
