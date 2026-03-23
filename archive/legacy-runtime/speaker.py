"""Speaker verification model for voiceprint-based authentication."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
import math


class TDNNBlock(nn.Module):
    """Time Delay Neural Network block for speaker encoding."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int = 1,
    ):
        super().__init__()
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            dilation=dilation,
            padding=(kernel_size - 1) // 2 * dilation,
        )
        self.bn = nn.BatchNorm1d(out_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.relu(self.bn(self.conv(x)))


class StatsPool(nn.Module):
    """Statistics pooling layer (mean and std)."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, channels, time)
        mean = torch.mean(x, dim=2)
        std = torch.std(x, dim=2)
        return torch.cat([mean, std], dim=1)


class SpeakerEncoder(nn.Module):
    """
    X-Vector style speaker encoder.

    Architecture: TDNN layers -> Stats Pooling -> FC layers -> Embedding
    """

    def __init__(
        self,
        input_dim: int = 80,
        embedding_dim: int = 256,
        num_speakers: Optional[int] = None,  # For training with classifier head
    ):
        super().__init__()

        self.input_dim = input_dim
        self.embedding_dim = embedding_dim

        # TDNN layers with increasing dilation
        self.tdnn_layers = nn.ModuleList([
            TDNNBlock(input_dim, 512, kernel_size=5, dilation=1),
            TDNNBlock(512, 512, kernel_size=3, dilation=2),
            TDNNBlock(512, 512, kernel_size=3, dilation=3),
            TDNNBlock(512, 512, kernel_size=1, dilation=1),
            TDNNBlock(512, 1500, kernel_size=1, dilation=1),
        ])

        # Statistics pooling
        self.stats_pool = StatsPool()

        # Embedding layers
        self.fc1 = nn.Linear(3000, embedding_dim)
        self.bn1 = nn.BatchNorm1d(embedding_dim)
        self.fc2 = nn.Linear(embedding_dim, embedding_dim)
        self.bn2 = nn.BatchNorm1d(embedding_dim)

        # Optional classifier for training
        self.num_speakers = num_speakers
        if num_speakers is not None:
            self.classifier = nn.Linear(embedding_dim, num_speakers)
        else:
            self.classifier = None

    def forward(
        self, x: torch.Tensor, return_embedding: bool = True
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input of shape (batch, n_mels, time) or (batch, 1, n_mels, time)
            return_embedding: Return speaker embedding instead of logits

        Returns:
            Speaker embedding or classification logits
        """
        # Handle 4D input (batch, 1, n_mels, time)
        if x.dim() == 4:
            x = x.squeeze(1)

        # TDNN layers
        for layer in self.tdnn_layers:
            x = layer(x)

        # Statistics pooling
        x = self.stats_pool(x)

        # Embedding layers
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.fc2(x)
        embedding = self.bn2(x)

        if return_embedding:
            return F.normalize(embedding, p=2, dim=1)

        if self.classifier is not None:
            return self.classifier(embedding)

        return embedding

    def extract_embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Extract speaker embedding."""
        return self.forward(x, return_embedding=True)


class ResNetSpeakerEncoder(nn.Module):
    """ResNet-based speaker encoder (alternative to TDNN)."""

    def __init__(
        self,
        input_dim: int = 80,
        embedding_dim: int = 256,
        channels: list = [64, 128, 256, 512],
    ):
        super().__init__()

        self.conv1 = nn.Conv2d(1, channels[0], kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm2d(channels[0])
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = self._make_layer(channels[0], channels[0], 2)
        self.layer2 = self._make_layer(channels[0], channels[1], 2, stride=2)
        self.layer3 = self._make_layer(channels[1], channels[2], 2, stride=2)
        self.layer4 = self._make_layer(channels[2], channels[3], 2, stride=2)

        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(channels[3], embedding_dim)
        self.bn_final = nn.BatchNorm1d(embedding_dim)

    def _make_layer(
        self, in_ch: int, out_ch: int, num_blocks: int, stride: int = 1
    ) -> nn.Module:
        layers = []
        layers.append(nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1))
        layers.append(nn.BatchNorm2d(out_ch))
        layers.append(nn.ReLU())

        for _ in range(1, num_blocks):
            layers.append(nn.Conv2d(out_ch, out_ch, 3, padding=1))
            layers.append(nn.BatchNorm2d(out_ch))
            layers.append(nn.ReLU())

        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.unsqueeze(1)

        x = F.relu(self.bn1(self.conv1(x)))
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)
        embedding = self.bn_final(x)

        return F.normalize(embedding, p=2, dim=1)


class SpeakerVerifier:
    """Speaker verification wrapper with enrollment and verification."""

    def __init__(
        self,
        encoder: nn.Module,
        device: str = "cpu",
        threshold: float = 0.5,
    ):
        self.encoder = encoder.to(device)
        self.device = device
        self.threshold = threshold
        self.enrolled_voices = {}  # speaker_id -> embedding

    def enroll(self, speaker_id: str, audio_features: torch.Tensor) -> torch.Tensor:
        """
        Enroll a new speaker.

        Args:
            speaker_id: Unique identifier for the speaker
            audio_features: Audio features (mel-spectrogram)

        Returns:
            Speaker embedding
        """
        with torch.no_grad():
            audio_features = audio_features.to(self.device)
            embedding = self.encoder.extract_embedding(audio_features)
            self.enrolled_voices[speaker_id] = embedding.cpu()

        return embedding

    def verify(
        self, audio_features: torch.Tensor, speaker_id: Optional[str] = None
    ) -> Tuple[float, bool]:
        """
        Verify speaker identity.

        Args:
            audio_features: Audio features to verify
            speaker_id: If provided, verify against this enrolled speaker

        Returns:
            (similarity_score, is_match)
        """
        with torch.no_grad():
            audio_features = audio_features.to(self.device)
            embedding = self.encoder.extract_embedding(audio_features)

            if speaker_id is not None:
                if speaker_id not in self.enrolled_voices:
                    raise ValueError(f"Speaker {speaker_id} not enrolled")

                enrolled_emb = self.enrolled_voices[speaker_id].to(self.device)
                similarity = F.cosine_similarity(embedding, enrolled_emb, dim=1)
                score = (similarity + 1) / 2  # Normalize to [0, 1]
                is_match = score > self.threshold
                return score.item(), is_match.item()
            else:
                # Compare against all enrolled speakers
                best_score = -1
                best_speaker = None

                for sid, enrolled_emb in self.enrolled_voices.items():
                    enrolled_emb = enrolled_emb.to(self.device)
                    similarity = F.cosine_similarity(embedding, enrolled_emb, dim=1)
                    score = (similarity + 1) / 2

                    if score > best_score:
                        best_score = score.item()
                        best_speaker = sid

                is_match = best_score > self.threshold
                return best_score, is_match

    def set_threshold(self, threshold: float):
        """Update verification threshold."""
        self.threshold = threshold

    def get_enrolled_speakers(self) -> list:
        """List enrolled speaker IDs."""
        return list(self.enrolled_voices.keys())

    def clear_enrollment(self, speaker_id: Optional[str] = None):
        """Clear enrollment data."""
        if speaker_id is None:
            self.enrolled_voices.clear()
        else:
            self.enrolled_voices.pop(speaker_id, None)


def compute_eer(
    scores_genuine: torch.Tensor, scores_impostor: torch.Tensor
) -> Tuple[float, float]:
    """
    Compute Equal Error Rate (EER) and threshold.

    Args:
        scores_genuine: Scores for genuine pairs
        scores_impostor: Scores for impostor pairs

    Returns:
        (eer, threshold)
    """
    all_scores = torch.cat([scores_genuine, scores_impostor])
    all_labels = torch.cat([
        torch.ones(len(scores_genuine)),
        torch.zeros(len(scores_impostor)),
    ])

    # Sort scores and compute FAR/FRR
    sorted_scores, indices = torch.sort(all_scores)
    sorted_labels = all_labels[indices]

    fnrs = torch.cumsum(sorted_labels, dim=0) / len(scores_genuine)
    fprs = 1 - torch.cumsum(1 - sorted_labels, dim=0) / len(scores_impostor)

    # Find threshold where FNR = FPR
    idx = torch.argmin(torch.abs(fnrs - fprs))
    eer = ((fnrs[idx] + fprs[idx]) / 2).item()
    threshold = sorted_scores[idx].item()

    return eer, threshold
