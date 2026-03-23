# VoiceTrust for OpenClaw — ROADMAP

> Status: restructure / open-source preparation + early MVP direction
> Scope: OpenClaw channel voice-message trust / speaker verification layer

---

## Current Goal

Build an **integration-first MVP** for OpenClaw that can evaluate whether an incoming voice message sounds like the enrolled owner, and return a usable trust/confidence signal to the channel pipeline.

At the current stage, the immediate focus is:
- restructuring `projects/voicetrust/` into a maintainable project shape
- preserving the imported remote prototype as a code asset
- preparing the repository for future open-source release
- avoiding unnecessary code churn before the public mainline is clarified

The project should **prefer proven open-source methods** over training custom models from scratch.

---

## Product Direction

VoiceTrust is intended to sit on the voice-message path:

1. incoming voice message
2. audio preprocessing
3. speaker verification / trust evaluation
4. structured trust output
5. OpenClaw decides how to use that signal

Target question:
- “Is this likely Kyleo speaking?”

Not target question (for now):
- “Can this single signal act as perfect biometric authentication?”

---

## MVP (current priority)

### MVP-1. Integration-first owner verification
- [ ] Support **single-owner enrollment**
- [ ] Support **incoming voice-message verification**
- [ ] Output structured fields suitable for OpenClaw integration, e.g.:
  - `speaker_match`
  - `similarity`
  - `trust_score`
  - `confidence`
  - `quality`
- [ ] Keep latency practical for real use in OpenClaw voice-message flows

### MVP-2. Reuse mature open-source building blocks
- [ ] Prefer **SpeechBrain ECAPA-TDNN** or similarly proven speaker verification backends
- [ ] Reuse existing audio preprocessing / VAD components where sensible
- [ ] Avoid training-first assumptions for the first working version
- [ ] Keep custom code focused on orchestration, scoring, persistence, and OpenClaw integration

### MVP-3. OpenClaw-facing integration shape
- [ ] Define how OpenClaw passes audio into VoiceTrust
- [ ] Define the result schema returned to OpenClaw
- [ ] Define failure/uncertain states, such as:
  - too short
  - too noisy
  - low confidence
  - no owner enrolled
- [ ] Make it easy to attach this to channel-mode voice-message handling

---

## What to Keep vs Avoid

### Keep
- [ ] Existing project structure if useful
- [ ] Config-driven pipeline design
- [ ] Trust score / orchestration layer if it remains practical
- [ ] Simple CLI/demo/testing path for local verification

### Avoid
- [ ] Randomly initialized custom production models
- [ ] Training-first architecture as the main path
- [ ] Reinventing solved speaker verification components
- [ ] Overengineering before OpenClaw integration is proven

---

## Practical Constraints

- [ ] Optimize for **Chinese / English / mixed voice-note** reality
- [ ] Prioritize **3–10 second** clips for early reliability
- [ ] Keep the first version practical on CPU
- [ ] Treat the current output as a **trust signal**, not a sole high-risk auth factor

---

## Next Enhancements (after MVP)

### E1. Long-audio stability
- [ ] Improve stability for longer audio, beyond the 3–10 second sweet spot
- [ ] Decide whether to chunk, crop, or pool embeddings over long clips
- [ ] Ensure long voice notes do not degrade reliability unnecessarily

### E2. Anti-spoofing
- [ ] Add a practical pre-trained anti-spoofing component
- [ ] Prefer a reuse-first approach (SpeechBrain / ASVspoof ecosystem / equivalent)
- [ ] Integrate spoof signals into trust scoring without blocking the MVP

### E3. Language awareness
- [ ] Add language ID or language-aware heuristics later
- [ ] Improve handling of Chinese / English / mixed speech patterns
- [ ] Use language awareness as an enhancer, not as a prerequisite for MVP

### E4. Voiceprint management
- [ ] Start with minimal owner persistence
- [ ] Later evolve toward a curated owner voiceprint set
- [ ] Prefer storing embeddings + metadata over keeping all raw audio
- [ ] Avoid collecting all conversation audio by default

---

## Voiceprint Management Direction (not blocking MVP)

Recommended long-term direction:
- small, curated owner voiceprint set
- controlled growth
- high-quality samples only
- candidate vs canonical samples later if needed
- no default “store every voice message forever” behavior

---

## Acceptance for the first meaningful milestone

The first meaningful milestone is reached when:
- [ ] a single owner can be enrolled
- [ ] an incoming audio sample can be checked against that owner
- [ ] the system returns a structured trust result
- [ ] the result is practical to consume from OpenClaw channel flows
- [ ] the implementation is based primarily on reused, proven open-source components

---

## Notes

- This is a real OpenClaw-facing feature, not a generic voice biometrics demo.
- OpenClaw integration matters more than elegant standalone ML architecture.
- A working, honest MVP beats a beautiful but unusable research path.
tters more than elegant standalone ML architecture.
- A working, honest MVP beats a beautiful but unusable research path.
