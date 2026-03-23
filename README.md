# VoiceTrust for OpenClaw

VoiceTrust is a voice-message trust layer for OpenClaw. It is designed to answer a practical question in channel workflows:

> Is this incoming voice message likely to be spoken by the enrolled owner?

The current project direction is **integration-first**:
- prefer proven open-source speaker verification components
- keep latency practical for real voice-note workflows
- return structured trust signals instead of pretending to be perfect biometric authentication

---

## Current Status

This repository area is currently in **restructure / open-source preparation**.

A remote prototype was imported as a code asset and is preserved under:

- `remote-import/snapshot_20260322/`

That imported snapshot is treated as the **source asset base**, not as the final public structure.
The current refactor goal is to gradually turn that prototype into a clean, maintainable, open-source-ready project under `projects/voicetrust/` **without over-modifying working code too early**.

---

## Product Goal

VoiceTrust sits on the voice-message path:

1. incoming voice message
2. audio preprocessing
3. speaker verification / trust evaluation
4. structured trust output
5. OpenClaw decides how to use that signal

Primary target question:
- **“Is this likely Kyleo speaking?”**

Non-goal for the first versions:
- perfect standalone biometric authentication
- training custom production models from scratch
- overengineered research architecture before integration is proven

---

## Current Technical Direction

The current imported prototype already validates a promising path:

- **Speaker verification:** SpeechBrain ECAPA-TDNN based flow
- **Voiceprint persistence:** simple embedding storage
- **Trust scoring:** composite structured output for downstream integration
- **Audio quality heuristics:** basic practical checks
- **Anti-spoofing:** currently limited / best-effort, not yet a trusted production-grade signal

The intended long-term direction is:
- treat **SpeechBrain as the primary engine** for VoiceTrust's speech-side trust layer
- keep VoiceTrust **independent from STT backend choice**
- keep mature OSS components where possible
- keep custom code focused on orchestration, scoring, persistence, and integration
- make OpenClaw consumption easy and explicit

---

## Repository Layout

Current project layout:

```text
projects/voicetrust/
├── README.md                     # public-facing overview
├── BLUEPRINT.md                  # internal architecture + refactor target
├── ROADMAP.md                    # project direction and milestones
├── LICENSE                       # repository license placeholder/selection
├── .gitignore                    # sane defaults for Python/audio/model caches
├── pyproject.toml                # modern packaging metadata (minimal for now)
├── docs/
│   ├── import-notes.md           # provenance of imported remote snapshot
│   ├── restructure-plan.md       # low-risk restructure plan
│   └── open-source-readiness.md  # what remains before public release
└── remote-import/
    └── snapshot_20260322/        # imported remote prototype asset
```

For now, the imported snapshot remains intact as the working code asset while we stabilize structure and documentation around it.

---

## Development Principle

At this phase:

- **preserve working imported code as an asset**
- **avoid unnecessary code churn**
- **improve project structure first**
- **separate legacy/training-era residue from the new mainline gradually**
- **prepare for open source by clarifying purpose, boundaries, and packaging**

---

## What Comes Next

The next steps are expected to be:

1. define the target public repository structure
2. identify which imported modules stay as mainline vs become legacy/reference
3. define the OpenClaw integration contract
4. add minimal smoke tests
5. tighten licensing / dependency / documentation for open-source release
6. keep a repeatable local run path under project-local `uv` environment

See also:
- `BLUEPRINT.md`
- `docs/restructure-plan.md`
- `docs/open-source-readiness.md`
- `docs/local-run-notes.md`
- `docs/upstream-policy.md`
- `docs/model-assets.md`
- `docs/speechbrain-engine-plan.md`
- `docs/language-and-owner-profiles.md`
- `ROADMAP.md`
