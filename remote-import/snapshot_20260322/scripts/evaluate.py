#!/usr/bin/env python3
"""
Evaluation script for VoiceTrust models.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
import numpy as np
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.detector import DeepfakeDetector, LightDetector
from features.extractor import FeatureExtractor
from data.dataset import AudioDataset, collate_fn
from utils.helpers import compute_eer, compute_tDCF, save_results


def evaluate_detector(model, dataloader, feature_extractor, device):
    """Evaluate deepfake detector."""
    model.eval()

    all_scores = []
    all_labels = []

    with torch.no_grad():
        for waveforms, labels in tqdm(dataloader, desc="Evaluating"):
            waveforms = waveforms.to(device)

            # Extract features
            batch_mels = []
            for wav in waveforms:
                mel = feature_extractor.extract_mel_spectrogram(wav)
                batch_mels.append(mel)
            mels = torch.stack(batch_mels)

            # Get predictions
            outputs = model(mels)
            probs = torch.softmax(outputs, dim=1)

            # Spoof probability (class 1)
            spoof_probs = probs[:, 1].cpu().numpy()

            all_scores.extend(spoof_probs)
            all_labels.extend(labels.numpy())

    all_scores = np.array(all_scores)
    all_labels = np.array(all_labels)

    # Compute metrics
    eer, threshold = compute_eer(all_scores, all_labels)
    tdcf = compute_tDCF(all_scores, all_labels)

    # Compute accuracy at threshold
    predictions = (all_scores >= threshold).astype(int)
    accuracy = np.mean(predictions == all_labels)

    metrics = {
        "eer": float(eer),
        "tDCF": float(tdcf),
        "threshold": float(threshold),
        "accuracy": float(accuracy),
    }

    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/detector.yaml")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--test-manifest", type=str, required=True)
    parser.add_argument("--output", type=str, default="evaluation_results.json")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    device = args.device

    # Load model
    checkpoint = torch.load(args.checkpoint, map_location=device)

    # Use LightDetector as default
    model = LightDetector().to(device)
    model.load_state_dict(checkpoint.get("model", checkpoint))

    # Feature extractor
    feature_extractor = FeatureExtractor(device=device)

    # Test dataset
    test_dataset = AudioDataset(
        manifest_path=args.test_manifest,
        sample_rate=16000,
        max_duration=10.0,
        augment=False,
    )

    from torch.utils.data import DataLoader
    test_loader = DataLoader(
        test_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=4,
        collate_fn=collate_fn,
    )

    print(f"Evaluating on {len(test_dataset)} samples...")

    # Evaluate
    metrics = evaluate_detector(model, test_loader, feature_extractor, device)

    print("\nResults:")
    for key, value in metrics.items():
        print(f"  {key}: {value:.4f}")

    # Save results
    save_results(metrics, args.output)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
