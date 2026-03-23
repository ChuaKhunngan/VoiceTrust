# SpeechBrain Engine Plan for VoiceTrust

## Core Decision

VoiceTrust adopts **SpeechBrain as the primary engine** for the speech-side trust layer.

This means:
- speaker verification / recognition is the current primary signal source
- future VAD / segmentation and language ID should preferentially reuse SpeechBrain-compatible building blocks where practical
- VoiceTrust remains a **trust layer**, not a speech-to-text system

## Boundary: VoiceTrust is independent from STT

VoiceTrust should stay logically independent from any downstream STT choice.

### VoiceTrust responsibilities
- accept an audio artifact
- preprocess / segment / assess audio for trust use
- verify whether the voice likely matches the enrolled owner
- produce structured trust output
- report uncertainty / failure states honestly

### VoiceTrust does NOT require a specific STT backend
- STT can be Whisper, cloud ASR, OpenAI, Gemini, SpeechBrain ASR, or anything else
- VoiceTrust should not depend on transcript availability for its core path
- transcript-aware heuristics can exist later, but the main trust path must remain audio-first

In other words:
> VoiceTrust should be able to run before, after, or fully separate from STT.

---

## Current main engine choice

### P1 mainline speaker engine
Current mainline:
- `speechbrain/spkrec-ecapa-voxceleb`

Reason:
- already integrated and locally validated
- owner vs non-owner separation is already observable
- practical latency and simple enrollment path
- suitable for single-owner trust workflows

### Current recommendation
Treat the current ECAPA path as:
- **main engine v1**
- default speaker verification backend until a stronger replacement is validated by A/B testing

Do not swap speaker models prematurely just for theoretical improvement.

---

## Planned feature rollout

## P1 — direct next integration

### 1. VAD / segmentation
Purpose:
- trim leading/trailing silence
- detect whether an audio sample contains enough usable speech
- improve enrollment quality
- improve verification stability on real voice notes

Expected integration value:
- cleaner owner enrollment
- better handling of long voice messages
- explicit failure states such as:
  - `insufficient_speech`
  - `too_short`
  - `too_sparse`

### 2. Keep speaker verification as the main trust axis
Purpose:
- continue to center the product around owner verification
- preserve existing output compatibility while improving stability

---

## P2 — second wave integration

### 3. Language ID
Purpose:
- add language-aware metadata
- help diagnose score shifts across Chinese / English / mixed speech
- support future threshold tuning by language or mixed-speech condition

Important note:
- language ID should initially be diagnostic / metadata-first
- do not overweight it in trust scoring until real data supports it

### 4. Multi-sample enrollment / voiceprint management
Purpose:
- move from single-sample owner enrollment to curated multi-sample enrollment
- reduce fragility from single-sample variation
- support future canonical / candidate sample management

Recommended direction:
- 3–5 curated owner samples
- aggregate embeddings or store sample set + metadata
- keep raw-audio retention conservative

---

## P3 — conditional enhancements

### 5. Enhancement / denoising
Use only when quality issues justify it.
Do not enable as an unconditional preprocessing default.

### 6. Source separation
Use only for multi-speaker / overlap situations.
Do not make it part of the normal mainline path.

### 7. Anti-spoofing
Still valuable, but not a blocker for the current VoiceTrust core.
Should be treated as a separate backend problem rather than as a reason to delay the rest of the trust layer.

---

## Suggested architecture shape

```text
Audio input
  -> quality / preprocessing gate
  -> VAD / segmentation
  -> speaker verification (ECAPA)
  -> optional language ID
  -> trust aggregation
  -> structured result
```

Conditional side-paths:
- noisy audio -> optional denoising
- overlapping speakers -> optional separation
- future spoof backend -> optional anti-spoofing

---

## Immediate build order

1. formalize STT independence in docs and interface language
2. integrate VAD / segmentation into the verification path
3. define failure states and structured metadata
4. add language ID as diagnostic metadata
5. evolve enrollment from single-sample to curated multi-sample owner support

---

## Success criteria for this phase

This phase succeeds when VoiceTrust can:
- take an audio file independent of STT
- determine whether usable speech exists
- verify against the enrolled owner reliably
- return structured result + failure states
- expose language-aware metadata without requiring transcript-based logic
