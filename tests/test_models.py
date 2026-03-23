"""Unit tests for VoiceTrust components."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import torch
import numpy as np
import pytest

from features.extractor import FeatureExtractor
from models.detector import DeepfakeDetector, LightDetector, RawNet2Detector
from models.speaker import SpeakerEncoder, ResNetSpeakerEncoder, SpeakerVerifier
from inference.pipeline import VoiceTrustPipeline


class TestFeatureExtractor:
    """Test feature extraction."""

    def test_initialization(self):
        extractor = FeatureExtractor()
        assert extractor.sample_rate == 16000
        assert extractor.n_mels == 80

    def test_mel_spectrogram(self):
        extractor = FeatureExtractor()
        waveform = torch.randn(1, 16000)  # 1 second
        mel = extractor.extract_mel_spectrogram(waveform)
        assert mel.shape[0] == 1
        assert mel.shape[1] == 80  # n_mels

    def test_mfcc(self):
        extractor = FeatureExtractor()
        waveform = torch.randn(1, 16000)
        mfcc = extractor.extract_mfcc(waveform)
        assert mfcc.shape[0] == 1
        assert mfcc.shape[1] == 20  # n_mfcc

    def test_f0_extraction(self):
        extractor = FeatureExtractor()
        # Create synthetic tone
        t = torch.linspace(0, 1, 16000)
        f0 = 150
        waveform = torch.sin(2 * np.pi * f0 * t)
        f0_result = extractor.extract_f0(waveform)
        assert "f0_mean" in f0_result
        assert "f0_std" in f0_result


class TestModels:
    """Test model architectures."""

    def test_light_detector(self):
        model = LightDetector()
        x = torch.randn(1, 80, 100)  # (batch, n_mels, time)
        output = model(x)
        assert output.shape == (1, 2)  # Binary classification

    def test_deepfake_detector(self):
        model = DeepfakeDetector()
        x = torch.randn(1, 1, 80, 100)
        output = model(x)
        assert output.shape == (1, 2)

        # Test embedding extraction
        embedding = model(x, return_embedding=True)
        assert embedding.shape == (1, 256)

    def test_speaker_encoder(self):
        model = SpeakerEncoder()
        x = torch.randn(1, 80, 100)  # (batch, n_mels, time)
        embedding = model(x)
        assert embedding.shape == (1, 256)

        # Check normalization
        norm = torch.norm(embedding, dim=1)
        assert torch.allclose(norm, torch.ones_like(norm), atol=1e-5)

    def test_resnet_speaker_encoder(self):
        model = ResNetSpeakerEncoder()
        x = torch.randn(1, 80, 100)
        embedding = model(x)
        assert embedding.shape == (1, 256)


class TestPipeline:
    """Test inference pipeline."""

    def test_pipeline_initialization(self):
        detector = LightDetector()
        speaker = SpeakerEncoder()
        pipeline = VoiceTrustPipeline(
            detector_model=detector,
            speaker_encoder=speaker,
        )
        assert pipeline.detector is not None
        assert pipeline.speaker_verifier is not None

    def test_trust_score_computation(self):
        detector = LightDetector()
        pipeline = VoiceTrustPipeline(detector_model=detector)

        # Test overall trust computation
        overall, confidence = pipeline._compute_overall_trust(
            deepfake_score=80.0,
            speaker_match=90.0,
            audio_quality=85.0,
            language_consistency=75.0,
        )
        assert 0 <= overall <= 100
        assert 0 <= confidence <= 100


class TestSpeakerVerifier:
    """Test speaker verification."""

    def test_enrollment_and_verification(self):
        encoder = SpeakerEncoder()
        verifier = SpeakerVerifier(encoder=encoder, device="cpu")

        # Create synthetic enrollment sample
        enrollment = torch.randn(1, 80, 100)
        verifier.enroll("test_speaker", enrollment)

        assert "test_speaker" in verifier.get_enrolled_speakers()

        # Verify
        test_sample = torch.randn(1, 80, 100)
        score, is_match = verifier.verify(test_sample, "test_speaker")
        assert 0 <= score <= 1
        assert isinstance(is_match, bool)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
