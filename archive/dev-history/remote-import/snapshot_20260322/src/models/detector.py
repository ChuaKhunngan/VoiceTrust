"""Deepfake detection model for synthetic speech detection."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple


class SqueezeExcitation(nn.Module):
    """Squeeze-and-Excitation block for channel attention."""

    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class ResidualBlock(nn.Module):
    """Residual block with optional squeeze-and-excitation."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        stride: int = 1,
        use_se: bool = True,
    ):
        super().__init__()
        self.conv1 = nn.Conv2d(
            in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.se = SqueezeExcitation(out_channels) if use_se else None

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(
                    in_channels, out_channels, kernel_size=1, stride=stride, bias=False
                ),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        if self.se is not None:
            out = self.se(out)
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class DeepfakeDetector(nn.Module):
    """
    CNN-based deepfake detector for synthetic speech detection.

    Architecture: ResNet-style CNN with squeeze-and-excitation blocks
    Input: Mel-spectrogram or raw waveform features
    Output: Binary classification (bonafide vs spoof)
    """

    def __init__(
        self,
        input_dim: int = 80,  # Number of mel bins
        num_classes: int = 2,  # Bonafide vs Spoof
        channels: list = [32, 64, 128, 256],
        embedding_dim: int = 256,
        dropout: float = 0.5,
        use_se: bool = True,
    ):
        super().__init__()

        self.input_dim = input_dim
        self.embedding_dim = embedding_dim

        # Initial convolution
        self.conv1 = nn.Conv2d(1, channels[0], kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(channels[0])
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        # Residual layers
        self.layer1 = self._make_layer(
            channels[0], channels[0], num_blocks=2, stride=1, use_se=use_se
        )
        self.layer2 = self._make_layer(
            channels[0], channels[1], num_blocks=2, stride=2, use_se=use_se
        )
        self.layer3 = self._make_layer(
            channels[1], channels[2], num_blocks=2, stride=2, use_se=use_se
        )
        self.layer4 = self._make_layer(
            channels[2], channels[3], num_blocks=2, stride=2, use_se=use_se
        )

        # Global pooling and embedding
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc_embedding = nn.Linear(channels[3], embedding_dim)
        self.dropout = nn.Dropout(dropout)

        # Classification head
        self.classifier = nn.Linear(embedding_dim, num_classes)

        self._initialize_weights()

    def _make_layer(
        self,
        in_channels: int,
        out_channels: int,
        num_blocks: int,
        stride: int,
        use_se: bool,
    ) -> nn.Sequential:
        layers = [
            ResidualBlock(in_channels, out_channels, stride=stride, use_se=use_se)
        ]
        for _ in range(1, num_blocks):
            layers.append(
                ResidualBlock(out_channels, out_channels, stride=1, use_se=use_se)
            )
        return nn.Sequential(*layers)

    def _initialize_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)

    def forward(
        self, x: torch.Tensor, return_embedding: bool = False
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch, 1, n_mels, time) or (batch, n_mels, time)
            return_embedding: If True, return embedding instead of logits

        Returns:
            Classification logits or embedding vector
        """
        # Add channel dimension if needed
        if x.dim() == 3:
            x = x.unsqueeze(1)

        # Feature extraction
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        # Pooling and embedding
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        embedding = self.fc_embedding(x)
        embedding = F.relu(embedding)

        if return_embedding:
            return embedding

        # Classification
        x = self.dropout(embedding)
        logits = self.classifier(x)

        return logits

    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Get probability scores for spoof detection."""
        logits = self.forward(x)
        return F.softmax(logits, dim=-1)

    def get_spoof_score(self, x: torch.Tensor) -> torch.Tensor:
        """Get spoof probability score (higher = more likely spoof)."""
        probs = self.predict_proba(x)
        # Return probability of spoof class (index 1)
        return probs[:, 1]


class RawNet2Detector(nn.Module):
    """
    Simplified RawNet2-style detector for raw waveform input.
    More computationally expensive but can capture subtle artifacts.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        num_classes: int = 2,
        embedding_dim: int = 256,
    ):
        super().__init__()

        # Sinc convolutions for learnable filterbanks
        self.sinc_conv = nn.Conv1d(
            in_channels=1,
            out_channels=80,
            kernel_size=251,
            stride=1,
            padding=125,
        )

        # Residual blocks
        self.res_blocks = nn.ModuleList([
            self._make_res_block(80, 80),
            self._make_res_block(80, 160),
            self._make_res_block(160, 160),
            self._make_res_block(160, 320),
        ])

        # Pooling and embedding
        self.avgpool = nn.AdaptiveAvgPool1d(1)
        self.fc_embedding = nn.Linear(320, embedding_dim)
        self.classifier = nn.Linear(embedding_dim, num_classes)

    def _make_res_block(self, in_ch: int, out_ch: int) -> nn.Module:
        return nn.Sequential(
            nn.Conv1d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm1d(out_ch),
            nn.LeakyReLU(0.2),
            nn.Conv1d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm1d(out_ch),
            nn.MaxPool1d(3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 2:
            x = x.unsqueeze(1)

        x = torch.abs(F.relu(self.sinc_conv(x)))

        for block in self.res_blocks:
            x = block(x)

        x = self.avgpool(x).squeeze(-1)
        embedding = F.relu(self.fc_embedding(x))
        logits = self.classifier(embedding)

        return logits


class LightDetector(nn.Module):
    """Lightweight detector for edge deployment."""

    def __init__(
        self,
        input_dim: int = 80,
        num_classes: int = 2,
        hidden_dim: int = 128,
    ):
        super().__init__()

        self.conv_layers = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 3:
            x = x.unsqueeze(1)
        x = self.conv_layers(x)
        return self.classifier(x)
