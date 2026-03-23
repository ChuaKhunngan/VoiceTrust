"""Utility functions for voice trust."""
import torch
import numpy as np
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("voicetrust")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_results(results: Dict[str, Any], output_path: str):
    """Save results to JSON."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)


def compute_eer(
    scores: np.ndarray, labels: np.ndarray
) -> tuple:
    """Compute Equal Error Rate."""
    # Sort by scores
    sorted_indices = np.argsort(scores)
    sorted_scores = scores[sorted_indices]
    sorted_labels = labels[sorted_indices]

    # Compute FPR and FNR at each threshold
    n_positive = np.sum(labels == 1)
    n_negative = np.sum(labels == 0)

    fnrs = np.cumsum(sorted_labels) / n_positive
    fprs = 1 - np.cumsum(1 - sorted_labels) / n_negative

    # Find EER
    eer_idx = np.argmin(np.abs(fnrs - fprs))
    eer = (fnrs[eer_idx] + fprs[eer_idx]) / 2
    threshold = sorted_scores[eer_idx]

    return eer, threshold


def compute_tDCF(
    scores: np.ndarray,
    labels: np.ndarray,
    p_target: float = 0.01,
    c_miss: float = 1.0,
    c_fa: float = 1.0,
) -> float:
    """Compute normalized tandem detection cost function."""
    # Find threshold that minimizes t-DCF
    thresholds = np.linspace(scores.min(), scores.max(), 1000)
    min_tdcf = float("inf")

    for threshold in thresholds:
        fa = np.sum((scores >= threshold) & (labels == 0)) / np.sum(labels == 0)
        miss = np.sum((scores < threshold) & (labels == 1)) / np.sum(labels == 1)

        tdcf = c_miss * p_target * miss + c_fa * (1 - p_target) * fa
        tdcf /= min(c_miss * p_target, c_fa * (1 - p_target))

        if tdcf < min_tdcf:
            min_tdcf = tdcf

    return min_tdcf


def get_device(prefer_cuda: bool = True) -> str:
    """Get best available device."""
    if prefer_cuda and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def count_parameters(model: torch.nn.Module) -> int:
    """Count trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


class AverageMeter:
    """Computes and stores the average and current value."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def ensure_dir(path: str) -> Path:
    """Ensure directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
