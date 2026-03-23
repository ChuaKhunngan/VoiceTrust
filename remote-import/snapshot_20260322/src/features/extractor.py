"""Audio feature extraction for voice trust analysis."""
import numpy as np
import torch
import torchaudio
import torchaudio.transforms as T
import librosa
from typing import Tuple, Optional, Dict


class FeatureExtractor:
    """Extract audio features for deepfake detection and speaker verification."""

    def __init__(
        self,
        sample_rate: int = 16000,
        n_mels: int = 80,
        n_fft: int = 512,
        hop_length: int = 160,
        win_length: int = 400,
        n_mfcc: int = 20,
        device: str = "cpu",
    ):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.win_length = win_length
        self.n_mfcc = n_mfcc
        self.device = device

        # Mel-spectrogram transform
        self.mel_transform = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            win_length=win_length,
            hop_length=hop_length,
            n_mels=n_mels,
            power=2.0,
        ).to(device)

        # MFCC transform
        self.mfcc_transform = T.MFCC(
            sample_rate=sample_rate,
            n_mfcc=n_mfcc,
            melkwargs={
                "n_fft": n_fft,
                "win_length": win_length,
                "hop_length": hop_length,
                "n_mels": n_mels,
            },
        ).to(device)

    def load_audio(self, audio_path: str, target_sr: Optional[int] = None) -> torch.Tensor:
        """Load and resample audio file."""
        if target_sr is None:
            target_sr = self.sample_rate

        waveform, sr = torchaudio.load(audio_path)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Resample if needed
        if sr != target_sr:
            resampler = T.Resample(sr, target_sr)
            waveform = resampler(waveform)

        return waveform

    def extract_mel_spectrogram(
        self, waveform: torch.Tensor, log_scale: bool = True
    ) -> torch.Tensor:
        """Extract mel-spectrogram features."""
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        mel_spec = self.mel_transform(waveform.to(self.device))

        if log_scale:
            mel_spec = torch.log(mel_spec + 1e-9)

        return mel_spec

    def extract_mfcc(self, waveform: torch.Tensor) -> torch.Tensor:
        """Extract MFCC features."""
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        mfcc = self.mfcc_transform(waveform.to(self.device))
        return mfcc

    def extract_lfcc(self, waveform: torch.Tensor, n_lfcc: int = 20) -> torch.Tensor:
        """Extract Linear Frequency Cepstral Coefficients (LFCC)."""
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)

        # Compute linear spectrogram
        spec = torch.abs(
            torch.stft(
                waveform.to(self.device).squeeze(0),
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                win_length=self.win_length,
                return_complex=True,
            )
        )

        # Compute LFCC using DCT
        lfcc = T.transforms.DCT(n_lfcc)(spec)
        return lfcc.unsqueeze(0)

    def extract_f0(self, waveform: torch.Tensor) -> Dict[str, np.ndarray]:
        """Extract fundamental frequency (F0) and related features using librosa."""
        if isinstance(waveform, torch.Tensor):
            waveform = waveform.cpu().numpy().squeeze()

        # Use librosa's PYIN for F0 estimation
        f0, voiced_flag, voiced_probs = librosa.pyin(
            waveform,
            fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"),
            sr=self.sample_rate,
        )

        # Compute statistics
        f0_voiced = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]

        return {
            "f0": f0,
            "voiced_flag": voiced_flag,
            "voiced_probs": voiced_probs,
            "f0_mean": np.nanmean(f0) if len(f0_voiced) > 0 else 0,
            "f0_std": np.nanstd(f0) if len(f0_voiced) > 0 else 0,
            "voiced_ratio": np.mean(voiced_flag) if voiced_flag is not None else 0,
        }

    def extract_all_features(
        self, waveform: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """Extract all features for deepfake detection."""
        features = {
            "mel_spectrogram": self.extract_mel_spectrogram(waveform),
            "mfcc": self.extract_mfcc(waveform),
            "lfcc": self.extract_lfcc(waveform),
            "f0": self.extract_f0(waveform),
        }
        return features

    def extract_embedding_features(self, waveform: torch.Tensor) -> torch.Tensor:
        """Extract features suitable for speaker embedding."""
        # For speaker verification, mel-spectrograms are typically used
        return self.extract_mel_spectrogram(waveform)

    def compute_delta(self, features: torch.Tensor, order: int = 1) -> torch.Tensor:
        """Compute delta features (derivatives)."""
        return torchaudio.transforms.ComputeDeltas()(features)

    def normalize_features(
        self, features: torch.Tensor, method: str = "cmvn"
    ) -> torch.Tensor:
        """Normalize features (CMVN or standard scaling)."""
        if method == "cmvn":
            # Cepstral Mean and Variance Normalization
            mean = torch.mean(features, dim=-1, keepdim=True)
            std = torch.std(features, dim=-1, keepdim=True)
            return (features - mean) / (std + 1e-9)
        elif method == "minmax":
            min_val = torch.min(features, dim=-1, keepdim=True)[0]
            max_val = torch.max(features, dim=-1, keepdim=True)[0]
            return (features - min_val) / (max_val - min_val + 1e-9)
        else:
            return features
