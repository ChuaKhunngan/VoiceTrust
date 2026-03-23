"""VoiceTrust package."""
from .features.extractor import FeatureExtractor
from .models.detector import DeepfakeDetector, LightDetector
from .models.speaker import SpeakerEncoder, SpeakerVerifier
from .inference.pipeline import VoiceTrustPipeline, TrustScore

__version__ = "0.1.0"

__all__ = [
    "FeatureExtractor",
    "DeepfakeDetector",
    "LightDetector",
    "SpeakerEncoder",
    "SpeakerVerifier",
    "VoiceTrustPipeline",
    "TrustScore",
]
