"""SpeechBrain model wrapper for speaker verification and anti-spoofing.

Uses pre-trained models from SpeechBrain hub:
- ECAPA-TDNN for speaker verification (trained on VoxCeleb)
- Anti-spoofing model for deepfake detection
"""
import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Dict, List
from pathlib import Path
import warnings

try:
    # SpeechBrain 1.0+ uses 'inference' instead of 'pretrained'
    try:
        from speechbrain.inference import EncoderClassifier, SpeakerRecognition
    except ImportError:
        from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
    from speechbrain.utils.metric_stats import EER
    SPEECHBRAIN_AVAILABLE = True
except ImportError:
    SPEECHBRAIN_AVAILABLE = False
    warnings.warn("SpeechBrain not installed. Speaker verification will not work.")


class SpeechBrainSpeakerVerifier:
    """Speaker verification using pre-trained ECAPA-TDNN from SpeechBrain."""

    # Pre-trained model sources
    VERIFICATION_MODELS = {
        "ecapa_voxceleb": "speechbrain/spkrec-ecapa-voxceleb",
        "ecapa_voxceleb_finetuned": "speechbrain/spkrec-ecapa-voxceleb",
        "xvector_voxceleb": "speechbrain/spkrec-xvector-voxceleb",
    }

    def __init__(
        self,
        model_name: str = "ecapa_voxceleb",
        device: str = "cpu",
        verification_threshold: float = 0.25,
        savedir: Optional[str] = None,
    ):
        """
        Initialize speaker verifier with pre-trained model.

        Args:
            model_name: Name of the pre-trained model to use
            device: Device to run on ('cpu' or 'cuda')
            verification_threshold: Cosine similarity threshold for verification
            savedir: Directory to save downloaded models (default: ~/.cache/speechbrain)
        """
        if not SPEECHBRAIN_AVAILABLE:
            raise RuntimeError("SpeechBrain is required. Install with: pip install speechbrain")

        self.device = device
        self.verification_threshold = verification_threshold
        self.model_name = model_name
        self.savedir = savedir or Path.home() / ".cache" / "speechbrain"

        # Map model name to source
        source = self.VERIFICATION_MODELS.get(model_name, model_name)

        print(f"Loading speaker verification model: {source}")
        print(f"Models will be cached in: {self.savedir}")

        try:
            # Load pre-trained speaker recognition model
            self.classifier = SpeakerRecognition.from_hparams(
                source=source,
                savedir=str(self.savedir / model_name.replace("/", "_")),
                run_opts={"device": device},
            )
            print(f"Speaker verification model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            raise

        # Storage for enrolled speakers
        self.enrolled_embeddings: Dict[str, torch.Tensor] = {}

    def enroll(self, speaker_id: str, audio_path: str) -> np.ndarray:
        """
        Enroll a new speaker by extracting their embedding.

        Args:
            speaker_id: Unique identifier for the speaker
            audio_path: Path to enrollment audio file

        Returns:
            Speaker embedding as numpy array
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Extract embedding
        signal = self.classifier.load_audio(audio_path)
        embedding = self.classifier.encode_batch(signal)

        # Store embedding
        self.enrolled_embeddings[speaker_id] = embedding.cpu()

        return embedding.squeeze().cpu().numpy()

    def enroll_embedding(self, speaker_id: str, embedding: np.ndarray) -> None:
        """
        Directly enroll a speaker embedding (useful for loading saved voiceprints).

        Args:
            speaker_id: Speaker identifier
            embedding: Pre-computed speaker embedding
        """
        self.enrolled_embeddings[speaker_id] = torch.from_numpy(embedding).unsqueeze(0)

    def verify(self, audio_path: str, speaker_id: str) -> Tuple[float, bool]:
        """
        Verify if audio matches enrolled speaker.

        Args:
            audio_path: Path to audio file to verify
            speaker_id: Speaker ID to verify against

        Returns:
            Tuple of (similarity_score, is_match)
            similarity_score: 0-1 score (higher = more similar)
            is_match: Boolean indicating if above threshold
        """
        if speaker_id not in self.enrolled_embeddings:
            raise ValueError(f"Speaker '{speaker_id}' not enrolled. Enroll first.")

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load and encode test audio
        signal = self.classifier.load_audio(audio_path)
        test_embedding = self.classifier.encode_batch(signal)

        # Get enrolled embedding
        enrolled_embedding = self.enrolled_embeddings[speaker_id].to(self.device)

        # Compute similarity using SpeechBrain's similarity function
        # Returns negative cosine distance, so we convert to positive similarity
        similarity = self.classifier.similarity(
            test_embedding.squeeze(1),
            enrolled_embedding.squeeze(1)
        )

        # Convert to 0-1 score (higher = more similar)
        # SpeechBrain similarity can be negative (cosine distance)
        score = (similarity.item() + 1) / 2

        # Determine match
        is_match = score > self.verification_threshold

        return score, is_match

    def verify_embeddings(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Compute similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1)
        """
        emb1 = torch.from_numpy(embedding1).unsqueeze(0).to(self.device)
        emb2 = torch.from_numpy(embedding2).unsqueeze(0).to(self.device)

        similarity = self.classifier.similarity(emb1, emb2)
        return (similarity.item() + 1) / 2

    def get_enrolled_speakers(self) -> List[str]:
        """Get list of enrolled speaker IDs."""
        return list(self.enrolled_embeddings.keys())

    def clear_enrollment(self, speaker_id: Optional[str] = None) -> None:
        """
        Clear enrollment data.

        Args:
            speaker_id: Specific speaker to clear, or None to clear all
        """
        if speaker_id is None:
            self.enrolled_embeddings.clear()
        else:
            self.enrolled_embeddings.pop(speaker_id, None)

    def save_voiceprint(self, speaker_id: str, path: str) -> None:
        """Save a speaker's voiceprint to disk."""
        if speaker_id not in self.enrolled_embeddings:
            raise ValueError(f"Speaker '{speaker_id}' not enrolled")

        embedding = self.enrolled_embeddings[speaker_id].squeeze().numpy()
        np.save(path, embedding)

    def load_voiceprint(self, speaker_id: str, path: str) -> None:
        """Load a speaker's voiceprint from disk."""
        embedding = np.load(path)
        self.enroll_embedding(speaker_id, embedding)


class AntiSpoofingDetector:
    """Anti-spoofing/deepfake detection using SpeechBrain."""

    # Pre-trained anti-spoofing models
    # Note: Some models may require authentication or have been moved
    SPOOFING_MODELS = {
        "ecapa_asvspoof": "speechbrain/asvspoof-audio-clf-ecapa",  # May require auth
        "lfcc_asvspoof": "speechbrain/asvspoof-audio-clf-lfcc",  # May require auth
        "rawnet2_asvspoof": "speechbrain/asvspoof2-audio-clf",  # Alternative
    }

    def __init__(
        self,
        model_name: str = "rawnet2_asvspoof",
        device: str = "cpu",
        savedir: Optional[str] = None,
    ):
        """
        Initialize anti-spoofing detector.

        Args:
            model_name: Name of the pre-trained model
            device: Device to run on
            savedir: Directory to save downloaded models
        """
        if not SPEECHBRAIN_AVAILABLE:
            raise RuntimeError("SpeechBrain is required")

        self.device = device
        self.savedir = savedir or Path.home() / ".cache" / "speechbrain"

        source = self.SPOOFING_MODELS.get(model_name, model_name)

        # Try multiple models in order of preference
        model_sources = [
            self.SPOOFING_MODELS.get(model_name, model_name),
            "speechbrain/asvspoof2-audio-clf",
            "speechbrain/asvspoof-audio-clf-lfcc",
        ]

        self.classifier = None
        for source in model_sources:
            try:
                print(f"  Trying model: {source}")
                self.classifier = EncoderClassifier.from_hparams(
                    source=source,
                    savedir=str(self.savedir / source.replace("/", "_")),
                    run_opts={"device": device},
                )
                print(f"Anti-spoofing model loaded successfully from {source}")
                break
            except Exception as e:
                print(f"    Failed: {e}")
                continue

        if self.classifier is None:
            print("Warning: Could not load any anti-spoofing model")
            print("Deepfake detection will use basic heuristics only")

    def analyze(self, audio_path: str) -> Dict[str, float]:
        """
        Analyze audio for spoofing/synthetic speech.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with:
                - spoof_probability: Probability of being synthetic (0-1)
                - bonafide_probability: Probability of being real (0-1)
                - is_synthetic: Boolean prediction
        """
        if self.classifier is None:
            return {
                "spoof_probability": 0.5,
                "bonafide_probability": 0.5,
                "is_synthetic": False,
                "error": "Model not loaded",
            }

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load and classify
        signal = self.classifier.load_audio(audio_path)
        prediction = self.classifier.classify_batch(signal)

        # Get probabilities
        # Output is typically [bonafide_prob, spoof_prob] or logits
        if hasattr(prediction, 'shape'):
            if prediction.dim() > 1:
                probs = F.softmax(prediction, dim=-1)
                bonafide_prob = probs[0, 0].item()
                spoof_prob = probs[0, 1].item() if probs.shape[1] > 1 else 1 - bonafide_prob
            else:
                # Binary classification output
                bonafide_prob = torch.sigmoid(prediction).item()
                spoof_prob = 1 - bonafide_prob
        else:
            # Handle tuple output from SpeechBrain
            bonafide_prob = 0.5
            spoof_prob = 0.5

        return {
            "spoof_probability": spoof_prob,
            "bonafide_probability": bonafide_prob,
            "is_synthetic": spoof_prob > 0.5,
        }


class AudioPreprocessor:
    """Audio preprocessing utilities."""

    def __init__(self, target_sample_rate: int = 16000):
        self.target_sample_rate = target_sample_rate

    def preprocess(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """
        Load and preprocess audio.

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (waveform_tensor, sample_rate)
        """
        try:
            import torchaudio
            waveform, sample_rate = torchaudio.load(audio_path)

            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            # Resample if needed
            if sample_rate != self.target_sample_rate:
                resampler = torchaudio.transforms.Resample(
                    sample_rate, self.target_sample_rate
                )
                waveform = resampler(waveform)
                sample_rate = self.target_sample_rate

            return waveform, sample_rate
        except Exception as e:
            raise RuntimeError(f"Failed to load audio: {e}")


def compute_trust_score(
    spoof_probability: float,
    speaker_match_score: Optional[float] = None,
    quality_score: float = 70.0,
    weights: Optional[Dict[str, float]] = None,
) -> Tuple[float, float, str]:
    """
    Compute overall trust score from component scores.

    Args:
        spoof_probability: Probability of being synthetic (0-1)
        speaker_match_score: Speaker verification score (0-1), None if not checked
        quality_score: Audio quality score (0-100)
        weights: Component weights (default: deepfake=0.4, speaker=0.3, quality=0.3)

    Returns:
        Tuple of (overall_score, confidence, trust_level)
        trust_level: "high", "medium", or "low"
    """
    # Default weights
    if weights is None:
        weights = {"deepfake": 0.4, "speaker": 0.3, "quality": 0.3}

    # Deepfake score (inverse of spoof probability)
    deepfake_score = (1 - spoof_probability) * 100

    # Compute weighted score
    if speaker_match_score is not None:
        overall = (
            weights["deepfake"] * deepfake_score +
            weights["speaker"] * speaker_match_score * 100 +
            weights["quality"] * quality_score
        )
    else:
        # Redistribute weights when speaker verification not used
        w_df = weights["deepfake"] + weights["speaker"] / 2
        w_q = weights["quality"] + weights["speaker"] / 2
        overall = w_df * deepfake_score + w_q * quality_score

    # Confidence based on score variance (simplified)
    scores = [deepfake_score, quality_score]
    if speaker_match_score is not None:
        scores.append(speaker_match_score * 100)

    variance = np.var(scores)
    confidence = max(0, min(100, 100 - variance / 10))

    # Trust level
    if overall >= 70:
        trust_level = "high"
    elif overall >= 40:
        trust_level = "medium"
    else:
        trust_level = "low"

    return overall, confidence, trust_level
