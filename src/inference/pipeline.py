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

    deepfake_score: float
    speaker_match: float
    audio_quality: float
    language_consistency: float
    overall_trust: float
    confidence: float
    is_synthetic: bool
    spoof_probability: float
    speaker_id: Optional[str] = None
    speech_duration: float = 0.0
    speech_ratio: float = 0.0
    vad_status: str = "unavailable"
    detected_language: Optional[str] = None
    language_confidence: float = 0.0
    failure_reason: Optional[str] = None
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
            "speech_duration": self.speech_duration,
            "speech_ratio": self.speech_ratio,
            "vad_status": self.vad_status,
            "detected_language": self.detected_language,
            "language_confidence": self.language_confidence,
            "failure_reason": self.failure_reason,
            "raw_scores": {
                "spoof_probability": self.raw_spoof_prob,
                "speaker_similarity": self.raw_speaker_score,
            },
        }


class VoiceTrustPipeline:
    """Main pipeline for voice trust verification using pre-trained models."""

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
        if not SPEECHBRAIN_AVAILABLE:
            raise RuntimeError(
                "SpeechBrain is required. Install with: pip install speechbrain"
            )

        self.device = device
        self.sample_rate = sample_rate
        self.weights = weights or {
            "deepfake": 0.4,
            "speaker": 0.3,
            "quality": 0.2,
            "language": 0.1,
        }
        self.spoof_threshold = spoof_threshold
        self.verification_threshold = verification_threshold
        self.preprocessor = AudioPreprocessor(target_sample_rate=sample_rate)
        self.min_speech_duration = 1.5
        self.min_speech_ratio = 0.25

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
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        speech_duration, speech_ratio, vad_status, failure_reason = self._analyze_speech(audio_path)
        deepfake_score, spoof_prob = self._analyze_deepfake(audio_path)
        speaker_match, raw_speaker_score = self._verify_speaker(audio_path, speaker_id)
        audio_quality = self._analyze_quality(audio_path)
        language_consistency, detected_language, language_confidence = self._analyze_language(
            audio_path, expected_language
        )

        if failure_reason in {"too_short", "insufficient_speech"}:
            speaker_match = -1.0
            raw_speaker_score = 0.0

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
            speech_duration=speech_duration,
            speech_ratio=speech_ratio,
            vad_status=vad_status,
            detected_language=detected_language,
            language_confidence=language_confidence,
            failure_reason=failure_reason,
            raw_spoof_prob=spoof_prob,
            raw_speaker_score=raw_speaker_score,
        )

    def _analyze_deepfake(self, audio_path: str) -> Tuple[float, float]:
        if self.spoofing_detector is None:
            warnings.warn("No spoofing detector available")
            return 50.0, 0.5
        try:
            result = self.spoofing_detector.analyze(audio_path)
            spoof_prob = result["spoof_probability"]
            bonafide_prob = result["bonafide_probability"]
            return bonafide_prob * 100, spoof_prob
        except Exception as e:
            warnings.warn(f"Deepfake analysis failed: {e}")
            return 50.0, 0.5

    def _analyze_speech(self, audio_path: str) -> Tuple[float, float, str, Optional[str]]:
        """Lightweight speech activity estimation for VoiceTrust."""
        try:
            waveform, sr = self.preprocessor.preprocess(audio_path)
            mono = waveform.squeeze(0)
            if mono.numel() == 0:
                return 0.0, 0.0, "empty", "insufficient_speech"

            total_duration = mono.shape[-1] / sr
            frame_size = max(1, int(0.03 * sr))
            hop_size = max(1, int(0.015 * sr))

            energies = []
            for start in range(0, max(1, mono.shape[-1] - frame_size + 1), hop_size):
                frame = mono[start:start + frame_size]
                if frame.numel() == 0:
                    continue
                energies.append(torch.sqrt(torch.mean(frame ** 2)).item())

            if not energies:
                return 0.0, 0.0, "no_frames", "insufficient_speech"

            energies_np = np.asarray(energies)
            max_energy = float(np.max(energies_np))
            if max_energy <= 1e-6:
                return 0.0, 0.0, "silence", "insufficient_speech"

            energy_threshold = max(0.01, max_energy * 0.2)
            speech_frames = energies_np > energy_threshold
            speech_ratio = float(np.mean(speech_frames))
            speech_duration = float(speech_ratio * total_duration)

            failure_reason = None
            if total_duration < 1.0:
                failure_reason = "too_short"
            elif speech_duration < self.min_speech_duration or speech_ratio < self.min_speech_ratio:
                failure_reason = "insufficient_speech"

            return speech_duration, speech_ratio, "ok", failure_reason
        except Exception as e:
            warnings.warn(f"Speech activity analysis failed: {e}")
            return 0.0, 0.0, "unavailable", None

    def _verify_speaker(self, audio_path: str, speaker_id: Optional[str]) -> Tuple[float, float]:
        if self.speaker_verifier is None or speaker_id is None:
            return -1.0, 0.0
        if speaker_id not in self.speaker_verifier.get_enrolled_speakers():
            return -1.0, 0.0
        try:
            score, _is_match = self.speaker_verifier.verify(audio_path, speaker_id)
            return score * 100, score
        except Exception as e:
            warnings.warn(f"Speaker verification failed: {e}")
            return -1.0, 0.0

    def _analyze_quality(self, audio_path: str) -> float:
        try:
            waveform, sr = self.preprocessor.preprocess(audio_path)
            duration = waveform.shape[-1] / sr
            rms = torch.sqrt(torch.mean(waveform ** 2)).item()
            peak = torch.max(torch.abs(waveform)).item()
            dynamic_range_db = 20 * np.log10(peak / (rms + 1e-10)) if peak > 0 else 0

            score = 100.0
            if duration < 1.0:
                score -= 20 * (1.0 - duration)
            if rms < 0.01:
                score -= 20
            if peak > 0.95:
                score -= 10
            if dynamic_range_db < 10:
                score -= 15
            return max(0.0, min(100.0, score))
        except Exception as e:
            warnings.warn(f"Quality analysis failed: {e}")
            return 70.0

    def _analyze_language(
        self, audio_path: str, expected_language: Optional[str]
    ) -> Tuple[float, Optional[str], float]:
        """Metadata-first placeholder until a real LID backend is integrated."""
        if expected_language is None:
            return 50.0, None, 0.0
        return 50.0, expected_language, 0.25

    def _compute_overall_trust(
        self,
        deepfake_score: float,
        speaker_match: float,
        audio_quality: float,
        language_consistency: float,
    ) -> Tuple[float, float]:
        if speaker_match >= 0:
            overall = (
                self.weights["deepfake"] * deepfake_score
                + self.weights["speaker"] * speaker_match
                + self.weights["quality"] * audio_quality
                + self.weights["language"] * language_consistency
            )
        else:
            w_df = self.weights["deepfake"] + self.weights["speaker"] / 2
            w_q = self.weights["quality"] + self.weights["speaker"] / 2
            overall = (
                w_df * deepfake_score
                + w_q * audio_quality
                + self.weights["language"] * language_consistency
            )

        scores = [deepfake_score, audio_quality, language_consistency]
        if speaker_match >= 0:
            scores.append(speaker_match)
        variance = np.var(scores)
        confidence = max(0.0, min(100.0, 100.0 - variance / 10))
        return overall, confidence

    def enroll_speaker(self, speaker_id: str, audio_path: str) -> np.ndarray:
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")
        return self.speaker_verifier.enroll(speaker_id, audio_path)

    def get_enrolled_speakers(self) -> list:
        if self.speaker_verifier is None:
            return []
        return self.speaker_verifier.get_enrolled_speakers()

    def save_voiceprint(self, speaker_id: str, path: str) -> None:
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")
        self.speaker_verifier.save_voiceprint(speaker_id, path)

    def load_voiceprint(self, speaker_id: str, path: str) -> None:
        if self.speaker_verifier is None:
            raise RuntimeError("Speaker verifier not initialized")
        self.speaker_verifier.load_voiceprint(speaker_id, path)

    def set_spoof_threshold(self, threshold: float) -> None:
        self.spoof_threshold = threshold

    def set_verification_threshold(self, threshold: float) -> None:
        self.verification_threshold = threshold
        if self.speaker_verifier is not None:
            self.speaker_verifier.verification_threshold = threshold
