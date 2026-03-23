# VoiceTrust — BLUEPRINT

## 1. Intent

VoiceTrust is an OpenClaw-facing voice trust component.

Its job is not to act as a magical identity oracle. Its job is to produce a **practical, structured trust signal** from incoming voice messages so higher-level OpenClaw workflows can make informed decisions.

Core product question:
- Is this incoming voice message likely to be spoken by the enrolled owner?

---

## 2. Current Reality

The current working code base was imported from a remote prototype snapshot:

- `remote-import/snapshot_20260322/`

That snapshot already appears to contain useful assets:
- a SpeechBrain-based speaker verification path
- trust scoring / pipeline orchestration
- CLI demo flow
- simple voiceprint persistence
- partial anti-spoofing integration attempts

However, the imported asset also appears to contain remnants of an older training-first direction:
- custom detector models
- custom speaker model code
- feature-engineering modules
- config sections oriented toward training

So the project is currently in a **pivoted-but-not-fully-cleaned** state.

---

## 3. Refactor Philosophy

### Guiding rule
Do **not** over-modify imported code prematurely.

### Instead
1. preserve imported snapshot provenance
2. define the intended public/mainline structure
3. move gradually from "imported prototype" to "maintained project"
4. keep working code runnable during transition
5. explicitly separate:
   - mainline runtime path
   - legacy / experimental / historical code

---

## 4. Target Structure (near-term)

Recommended near-term structure:

```text
projects/voicetrust/
├── README.md
├── BLUEPRINT.md
├── ROADMAP.md
├── LICENSE
├── .gitignore
├── pyproject.toml
├── docs/
│   ├── import-notes.md
│   ├── restructure-plan.md
│   ├── open-source-readiness.md
│   └── integration-contract.md   # later
├── remote-import/
│   └── snapshot_20260322/
├── src/                          # later, when mainline package is promoted
├── tests/                        # later, minimal smoke tests first
└── examples/                     # later, enrollment/verification examples
```

Important:
- `remote-import/snapshot_20260322/` remains the preserved imported asset.
- We should not pretend it is already the final public package layout.

---

## 5. Mainline vs Legacy (intended split)

### Mainline candidates
These likely represent the near-term product path and should eventually become the canonical public runtime path:
- SpeechBrain-based speaker verification wrapper
- trust scoring pipeline
- simple CLI/demo enrollment + verification flow
- voiceprint persistence logic

### Legacy / reference candidates
These may still be useful as reference assets, but should not define the public product story unless they are actively revived:
- custom detector training code
- custom speaker encoder training code
- feature-extraction modules tied to training-first assumptions
- config sections describing training loops/checkpoints for unused paths

---

## 6. OpenClaw Integration Shape (high level)

Expected long-term interaction:

### Input
- audio path or prepared audio artifact from OpenClaw voice-message handling
- enrolled owner identifier (initially single-owner is fine)
- optional config/runtime hints

### Output
Structured trust result, e.g.:
- `speaker_match`
- `similarity`
- `trust_score` / `overall_trust`
- `confidence`
- `quality`
- failure / uncertainty state

### Important behavior
The first production-facing version should be honest about uncertainty:
- no owner enrolled
- clip too short
- low quality
- spoof detector unavailable
- verification inconclusive

---

## 7. Open-Source Preparation Goals

Before public release, the project should have:
- clear purpose and scope
- license selection and attribution hygiene
- dependency story that others can actually install
- documented limitations
- explicit provenance of imported prototype code
- minimal tests / smoke validation
- example usage paths
- clean distinction between supported path and historical residue

---

## 8. Immediate Build Order

Recommended order of work:

1. **structure first**
   - docs
   - package metadata
   - ignore rules
   - license
   - import provenance
2. **mainline clarification**
   - document which imported code is current-path vs historical
3. **integration contract**
   - define how OpenClaw should call VoiceTrust
4. **smoke validation**
   - ensure imported path still runs after restructuring
5. **gradual code promotion**
   - only then start moving selected modules into stable public package layout

---

## 9. Non-Goals for this refactor step

At this exact stage, avoid:
- large algorithm rewrites
- aggressive file moves that break the imported prototype prematurely
- replacing working code just for elegance
- pretending anti-spoofing is production-ready when it is not
- training-first expansion before OpenClaw integration is proven
