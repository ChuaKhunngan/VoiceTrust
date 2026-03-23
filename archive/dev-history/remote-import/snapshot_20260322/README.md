# VoiceTrust for OpenClaw

A voice message trust verification system using pre-trained SpeechBrain models. Optimized for Chinese/English voice scenarios. Detects synthetic speech (where models available), verifies speaker authenticity, and provides trust scores for voice messages.

## Core Capabilities

1. **Speaker Verification** ✅ Working - Uses SpeechBrain ECAPA-TDNN (pre-trained on VoxCeleb)
2. **Deepfake Detection** ⚠️ Limited - Anti-spoofing models require HuggingFace authentication
3. **Audio Quality Analysis** ✅ Working - Basic heuristics for audio artifacts
4. **Trust Scoring** ✅ Working - Composite score based on available signals

## Architecture

```
voice-trust/
├── src/
│   ├── models/
│   │   └── speechbrain_wrapper.py   # SpeechBrain integration
│   ├── inference/
│   │   └── pipeline.py              # Trust scoring pipeline
│   └── features/
│       └── extractor.py             # Audio preprocessing (kept for compatibility)
├── scripts/
│   └── demo.py                      # CLI demo with enrollment/verification
├── data/
│   └── voiceprints/                 # Persistent speaker voiceprints
├── configs/
│   └── pipeline.yaml                # Configuration
└── requirements.txt                 # Dependencies
```

## Quick Start

```bash
# Setup environment
cd /home/cky/codeleader/voice-trust
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Create test audio
python scripts/demo.py --create-demo test.wav

# Enroll a speaker (single-owner pattern)
python scripts/demo.py --audio test.wav --speaker owner --enroll

# Verify incoming voice message
python scripts/demo.py --audio test.wav --speaker owner

# List enrolled speakers
python scripts/demo.py --list-speakers

# Output as JSON for integration
python scripts/demo.py --audio test.wav --speaker owner --json
```

## Usage Examples

### Single-Owner Enrollment (Recommended for OpenClaw)

```bash
# 1. Owner records enrollment audio (5-10 seconds of speech)
# 2. Enroll the owner
python scripts/demo.py --audio owner_enrollment.wav --speaker owner --enroll

# 3. For each incoming voice message
python scripts/demo.py --audio incoming_message.wav --speaker owner
```

### Output Format (JSON)

```json
{
  "deepfake_score": 50.0,
  "speaker_match": 100.0,
  "audio_quality": 75.0,
  "language_consistency": 50.0,
  "overall_trust": 70.0,
  "confidence": 57.03,
  "is_synthetic": false,
  "spoof_probability": 0.5,
  "speaker_id": "owner",
  "raw_scores": {
    "spoof_probability": 0.5,
    "speaker_similarity": 1.0
  }
}
```

## Trust Score Interpretation

| Overall Score | Trust Level | Recommendation |
|---------------|-------------|----------------|
| 80-100 | HIGH | Message appears authentic |
| 40-80 | MEDIUM | Review with caution |
| 0-40 | LOW | Synthetic speech likely, verify independently |

## Technical Details

### Speaker Verification
- **Model**: SpeechBrain ECAPA-TDNN (pre-trained on VoxCeleb2)
- **Embedding Size**: 192 dimensions
- **Verification Method**: Cosine similarity
- **Default Threshold**: 0.25 (tune based on use case)
- **Voiceprint Storage**: NumPy arrays in `data/voiceprints/`

### Anti-Spoofing (Deepfake Detection)
- **Status**: Requires HuggingFace authentication for SpeechBrain models
- **Fallback**: Basic heuristics based on audio quality metrics
- **Alternative**: Can be disabled, trust score based on speaker verification + quality

### Audio Quality Metrics
- Duration check (penalizes very short clips)
- Signal level analysis
- Clipping detection
- Dynamic range analysis

## Configuration

Edit `configs/pipeline.yaml` to customize:

```yaml
pipeline:
  weights:
    deepfake: 0.4
    speaker: 0.3
    quality: 0.2
    language: 0.1

  thresholds:
    spoof: 0.5
    verification: 0.25
```

## Integration for OpenClaw Channels

```python
from inference.pipeline import VoiceTrustPipeline

# Initialize
pipeline = VoiceTrustPipeline(device="cpu")

# Load enrolled owner voiceprint
pipeline.load_voiceprint("owner", "data/voiceprints/owner.npy")

# Verify incoming message
result = pipeline.analyze_audio(
    audio_path="incoming.wav",
    speaker_id="owner"
)

# Use result.overall_trust for channel decision
if result.overall_trust >= 70:
    print("Message verified - forward to user")
elif result.overall_trust >= 40:
    print("Suspicious - flag for review")
else:
    print("Likely spoof - reject or require additional verification")
```

## Known Limitations

1. **Anti-Spoofing**: SpeechBrain ASVspoof models require HuggingFace authentication. For production, consider:
   - Setting up HuggingFace token authentication
   - Using alternative anti-spoofing solutions
   - Relying on speaker verification + audio quality heuristics

2. **Language ID**: Not implemented yet. All audio treated as language-neutral.

3. **Audio Duration**: Optimal performance with 3-10 second clips

## Dependencies

- Python 3.8+
- PyTorch 2.0+
- SpeechBrain 1.0+
- soundfile, librosa (audio I/O)
- See `requirements.txt` for full list

## Model Caching

Pre-trained models are downloaded on first run and cached in:
- `~/.cache/speechbrain/` (models)
- `data/voiceprints/` (enrolled speaker embeddings)

## License

This project uses pre-trained models from SpeechBrain, which are subject to their respective licenses.
