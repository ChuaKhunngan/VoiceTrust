# Language ID and Owner Profiles

## Language ID

Current status:
- VoiceTrust now reserves stable output fields for language-aware metadata:
  - `detected_language`
  - `language_confidence`
  - `language_consistency`
- Current local mainline uses a metadata-first placeholder path
- This keeps the public interface stable while a stronger SpeechBrain-based LID backend is integrated later

Design rule:
- language metadata should be diagnostic-first
- do not overweight it in trust scoring until validated on real mixed-language owner audio

## Multi-sample owner enrollment

VoiceTrust now includes a first owner-profile storage layer:
- per-owner directory under `data/owners/<speaker_id>/`
- sample embeddings stored individually
- aggregate embedding stored as `aggregate.npy`
- profile metadata stored in `profile.json`

Current aggregation strategy:
- centroid-style mean aggregation of enrolled sample embeddings

Why this matters:
- reduces single-sample fragility
- prepares the project for curated 3–5 sample owner enrollment
- stays simple and open-source friendly

## CLI usage

### Append owner sample
```bash
./.venv/bin/python scripts/demo.py \
  --audio path/to/owner_sample.wav \
  --speaker owner \
  --enroll-sample \
  --json
```

### Verify using aggregated owner profile
```bash
./.venv/bin/python scripts/demo.py \
  --audio path/to/incoming.wav \
  --speaker owner \
  --json
```

If an owner profile exists, the CLI now prefers the aggregated owner profile over the legacy single-file `data/voiceprints/<speaker>.npy` path.
