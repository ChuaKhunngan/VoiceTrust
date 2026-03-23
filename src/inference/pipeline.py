"""Inference pipeline for VoiceTrust - integration with SpeechBrain pre-trained models.

This is the refactored version using proven open-source models:
- SpeechBrain ECAPA-TDNN for speaker verification
- SpeechBrain anti-spoofing model for deepfake detection
"""
import torch
import numpy as np
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import warnings

try:
    from models.speechbrain_wrapper import (
        SpeechBrainSpeakerVerifier,
        AntiSpoofingDetector,
        compute_trust_score,
        AudioPreprocessor,
    )
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False
    warnings.warn("SpeechBrain wrapper not available. Pipeline will not function.")


@dataclass
class TrustScore:
    """Trust analysis results."""

    # Component scores (0-100, higher = more trustworthy)
    deepfake_score: float  # 100 = definitely bonafide, 0 = definitely synthetic
    speaker_match: float  # 100 = verified match, 0 = no match, -1 = not checked
    audio_quality: float  # 100 = high quality natural audio
    language_consistency: float  # 100 = consistent with expected language

    # Final score
    overall_trust: float  # Weighted combination
    confidence: float  # Confidence in the assessment

    # Details
    is_synthetic: bool
    spoof_probability: float
    speaker_id: Optional[str] = None

    # Raw scores for debugging
    raw_spoof_prob: float = 0.0
    raw_speaker_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deepfake_score": self.deepfake_score,
            "speaker_match": self.speaker_match,
            "audio_quality": self.audio_quality,
            "language_consistency": self.language_consistency,
            "overall_trust": self.overall_trust,
            "confidence": self.confidence,
            "is_synthetic": self.is_synthetic,
            "spoof_probability": self.spoof_probability,
            "speaker_id": self.speaker_id,
            "raw_scores": {
                "spoof_probability": self.raw_spoof_prob,
                "speaker_similarity": self.raw_speaker_score,
            },
        }


class VoiceTrustPipeline:
    """
    Main pipeline for voice trust verification using pre-trained models.

    Uses SpeechBrain models:
    - ECAPA-TDNN for speaker verification
    - Pre-trained classifier for anti-spoofing
    """

    def __init__(
        self,
        device: str = "cpu",
        sample_rate: int = 16000,
        verification_threshold: float = 0.25,
        spoof_threshold: float = 0.5,
        weights: Optional[Dict[str, float]] = None,
        speaker_model: str = "ecapa_voxceleb",
        spoofing_model: str = "rawnet2_asvspoof",
    ):
        """
        Initialize VoiceTrust pipeline.

        Args:
            device: Device to run on ('cpu' or 'cuda')
            sample_rate: Target sample rate for audio
            verification_threshold: Threshold for speaker verification (0-1)
            spoof_threshold: Threshold for spoof detection (0-1)
            weights: Component weights for trust scoring
            speaker_model: Pre-trained speaker model name
            spoofing_model: Pre-trained anti-spoofing model name
        """
        if not SPEECHBRAIN_AVAILABLE:
            raise RuntimeError(
                "SpeechBrain is required. Install with: pip install speechbrain"
            )

        self.device = device
        self.sample_rate = sample_rate

        # Default weights for trust score combination
        self.weights = weights or {
            "deepfake": 0.4,
            "speaker": 0.3,
            "quality": 0.2,
            "language": 0.1,
        }

        # Thresholds
        self.spoof_threshold = spoof_threshold
        self.verification_threshold = verification_threshold

        # Initialize preprocessor
        self.preprocessor = AudioPreprocessor(target_sample_rate=sample_rate)

        # Initialize models (will download on first run)
        print("Initializing VoiceTrust pipeline...")
        print(f"Device: {device}")

        try:
            self.speaker_verifier = SpeechBrainSpeakerVerifier(
                model_name=speaker_model,
                device=device,
                verification_threshold=verification_threshold,
            )
        except Exception as e:
            print(f"Warning: Could not load speaker verification model: {e}")
            self.speaker_verifier = None

        try:
            self.spoofing_detector = AntiSpoofingDetector(
                model_name=spoofing_model,
                device=device,
            )
        except Exception as e:
            print(f"Warning: Could not load anti-spoofing model: {e}")
            self.spoofing_detector = None

        print("Pipeline initialized successfully")

    def analyze_audio(
        self,
        audio_path: str,
        speaker_id: Optional[str] = None,
        expected_language: Optional[str] = None,
    ) -> TrustScore:
        """
        Analyze audio file and return trust scores.

        Args:
            audio_path: Path to audio file
            speaker_id: Optional speaker ID to verify against
            expected_language: Optional expected language ("chinese", "english")

        Returns:
            TrustScore object with all analysis results
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Run analyses
        deepfake_score, spoof_prob = self._analyze_deepfake(audio_path)
        speaker_match, raw_speaker_score = self._verify_speaker(audio_path, speaker_id)
        audio_quality = self._analyze_quality(audio_path)
        language_consistency = self._analyze_language(audio_path, expected_language)

        # Compute overall trust score
        overall_trust, confidence = self._compute_overall_trust(
            deepfake_score=deepfake_score,
            speaker_match=speaker_match,
            audio_quality=audio_quality,
            language_consistency=language_consistency,
        )

        return TrustScore(
            deepfake_score=deepfake_score,
            speaker_match=speaker_match,
            audio_quality=audio_quality,
            language_consistency=language_consistency,
            overall_trust=overall_trust,
            confidence=confidence,
            is_synthetic=spoof_prob > self.spoof_threshold,
            spoof_probability=spoof_prob,
            speaker_id=speaker_id,
            raw_spoof_prob=spoof_prob,
            raw_speaker_score=raw_speaker_score,
        )

    def _analyze_deepfake(self, audio_path: str) -> Tuple[float, float]:
        """
        Analyze audio for deepfake/synthetic speech.

        Returns:
            Tuple of (trust_score, spoof_probability)
            trust_score: 0-100 (higher = more trustworthy)
            spoof_probability: 0-1 (higher = more likely synthetic)
        """
        if self.spoofing_detector is None:
            warnings.warn("No spoofing detector available")
            return 50.0, 0.5

        try:
            result = self.spoofing_detector.analyze(audio_path)
            spoof_prob = result["spoof_probability"]
            bonafide_prob = result["bonafide_probability"]

            # Convert to trust score (0-100)
            trust_score = bonafide_prob * 100

            return trust_score, spoof_prob
        except Exception as e:
            warnings.warn(f"Deepfake analysis failed: {e}")
            return 50.0, 0.5

    def _verify_speaker(
        self, audio_path: str, speaker_id: Optional[str]
    ) -> Tuple[float, float]:
        """
        Verify speaker identity.

        Returns:
            Tuple of (match_score, raw_similarity)
            match_score: 0-100 (higher = better match), -1 if not checked
            raw_similarity: Raw similarity value (0-1)
        """
        if self.speaker_verifier is None or speaker_id is None:
            return -1.0, 0.0

        if speaker_id not in self.speaker_verifier.get_enrolled_speakers():
            return -1.0, 0.0

        try:
            score, is_match = self.speaker_verifier.verify(audio_path, speaker_id)
            return score * 100, score
        except Exception as e:
            warnings.warn(f"Speaker verification failed: {e}")
            return -1.0, 0.0

    def _analyze_quality(self, audio_path: str) -> float:
        """
        Analyze audio quality metrics.

        Returns:
            Quality score (0-100)
        """
        try:
            # Load audio for analysis
            waveform, sr = self.preprocessor.preprocess(audio_path)

            # Compute basic quality metrics
            # Duration check
            duration = waveform.shape[-1] / sr

            # Signal level
            rms = torch.sqrt(torch.mean(waveform ** 2)).item()

            # Peak level
            peak = torch.max(torch.abs(waveform)).item()

            # Dynamic range
            if peak > 0:
                dynamic_range_db = 20 * np.log10(peak / (rms + 1e-10))
            else:
                dynamic_range_db = 0

            # Score computation
            score = 100.0

            # Penalize very short clips
            if duration < 1.0:
                score -= 20 * (1.0 - duration)

            # Penalize very low volume
            if rms < 0.01:
                score -= 20

            # Penalize clipping
            if peak > 0.95:
                score -= 10

            # Penalize low dynamic range (possible synthetic)
            if dynamic_range_db < 10:
                score -= 15

            return max(0.0, min(100.0, score))
        except Exception as e:
            warnings.warn(f"Quality analysis failed: {e}")
            return 70.0  # Default neutral score

    def _analyze_language(
        self, audio_path: str, expected_language: Optional[str]
    ) -> float:
        """
        Analyze language consistency.

        Returns:
            Consistency score (0-100), 50 if not checked
        """
        if expected_language is None:
            return 50.0

        # Language ID not implemented yet - would require additional model
        # For now, return neutral score
        return 50.0

    def _compute_overall_trust(
        self,
        deepfake_score: float,
        speaker_match: float,
        audio_quality: float,
        language_consistency: float,
    ) -> Tuple[float, float]:
        """
        Compute overall trust score from components.

        Returns:
            Tuple of (overall_score, confidence)
        """
        # Weight the scores
        if speaker_match >= 0:
            # We have speaker verification
            overall = (
                self.weights["deepfake"] * deepfake_score +
                self.weights["speaker"] * speaker_match +
                self.weights["quality"] * audio_quality +
                self.weights["language"] * language_consistency
            )
        else:
            # No speaker verification - redistribute weights
            w_df = self.weights["deepfake"] + self.weights["speaker"] / 2
            w_q = self.weights["quality"] + self.weights["speaker"] / 2
            overall = (
                w_df * deepfake_score +
                w_q * audio_quality +
                self.weights["language"] * language_consistency
            )

        # Confidence based on score variance
        scores = [deepfake_score, audio_quality, language_consistency]
        if speaker_match >= 0:
            scores.append(speaker_match)

        variance = np.var(scores)
        confidence = max(0.0, min(100.0, 100.0 - variance / 10))

        return overall, confidence

    def enroll_speaker(self, speaker_id: str, audio_path: str) -> np.ndarray:
        """
        Enroll a new speaker.

        Args:
            speaker_id: Unique identifier for the speaker
            audio_path: Path to enrollment audio file

        Returns:
            Speaker embedding
        """
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")

        return self.speaker_verifier.enroll(speaker_id, audio_path)

    def get_enrolled_speakers(self) -> list:
        """Get list of enrolled speakers."""
        if self.speaker_verifier is None:
            return []
        return self.speaker_verifier.get_enrolled_speakers()

    def save_voiceprint(self, speaker_id: str, path: str) -> None:
        """Save a speaker's voiceprint to disk."""
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")
        self.speaker_verifier.save_voiceprint(speaker_id, path)

    def load_voiceprint(self, speaker_id: str, path: str) -> None:
        """Load a speaker's voiceprint from disk."""
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")
        self.speaker_verifier.load_voiceprint(speaker_id, path)

    def set_spoof_threshold(self, threshold: float) -> None:
        """Set the threshold for spoof detection."""
        self.spoof_threshold = threshold

    def set_verification_threshold(self, threshold: float) -> None:
        """Set the threshold for speaker verification."""
        self.verification_threshold = threshold
        if self.speaker_verifier is not None:
            self.speaker_verifier.verification_threshold = threshold
