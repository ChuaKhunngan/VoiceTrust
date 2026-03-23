# Upstream Policy

## Primary upstream

VoiceTrust uses **SpeechBrain 1.0.3** as its primary speech engine upstream.

Current policy:
- pin upstream package version to `speechbrain==1.0.3`
- build VoiceTrust as a thin, explicit trust layer on top of upstream capabilities
- avoid copying or re-implementing SpeechBrain internals unless absolutely necessary
- keep local compatibility work inside VoiceTrust wrappers, not by forking upstream prematurely
- treat **SpeechBrain 1.0.3 official package / repository structure** as the only engine entrypoint
- avoid introducing **Hugging Face runtime dependency** as a product requirement

## Runtime dependency boundary

VoiceTrust should progressively move toward:
- SpeechBrain code as the engine runtime
- locally controlled model/config assets
- local-path loading where possible

VoiceTrust should progressively move away from:
- runtime dependence on remote Hugging Face model names
- model discovery that depends on external hosted repos remaining stable
- product behavior that breaks because a third-party hosted model page changes

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
- official task/recipe structure that VoiceTrust can map onto

### VoiceTrust responsibility
- owner verification workflow
- trust scoring and decision metadata
- VAD / language-aware integration choices
- failure-state semantics
- OpenClaw-facing interface
- STT-independent audio trust contract
- local asset packaging strategy for reproducible deployment

## Scope clarification

VoiceTrust currently cares about:
- speaker verification / recognition
- VAD / segmentation
- language identification (LID)
- optional quality / denoising / separation support later

VoiceTrust does **not** currently target Spoken Language Understanding (SLU) tasks such as:
- intent classification
- command understanding benchmarks like SLURP / Fluent Speech Commands / Timers-and-Such / MEDIA

## Upgrade policy

Future upgrades beyond 1.0.3 should be deliberate and gated by:
- passing local smoke tests
- no regression in owner vs non-owner separation
- wrapper compatibility review
- changelog / release note review where available
