"""Models module - SpeechBrain integration for VoiceTrust."""

# SpeechBrain-based implementations (recommended)
try:
    from .speechbrain_wrapper import (
        SpeechBrainSpeakerVerifier,
        AntiSpoofingDetector,
        AudioPreprocessor,
        compute_trust_score,
    )
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False

# Legacy custom models (kept for reference but not recommended)
from .detector import DeepfakeDetector, LightDetector, RawNet2Detector
from .speaker import SpeakerEncoder, ResNetSpeakerEncoder, SpeakerVerifier

__all__ = [
    # SpeechBrain wrappers (recommended)
    "SpeechBrainSpeakerVerifier",
    "AntiSpoofingDetector",
    "AudioPreprocessor",
    "compute_trust_score",
    "SPEECHBRAIN_AVAILABLE",
    # Legacy models (not recommended for production)
    "DeepfakeDetector",
    "LightDetector",
    "RawNet2Detector",
    "SpeakerEncoder",
    "ResNetSpeakerEncoder",
    "SpeakerVerifier",
]
