"""Training script for deepfake detection model."""
import argparse
import json
import os
from pathlib import Path
from typing import Dict

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import yaml
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.detector import DeepfakeDetector, LightDetector
from features.extractor import FeatureExtractor
from data.dataset import AudioDataset, collate_fn


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    device: str,
    feature_extractor: FeatureExtractor,
    epoch: int,
) -> Dict[str, float]:
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    pbar = tqdm(dataloader, desc=f"Epoch {epoch}")
    for waveforms, labels in pbar:
        waveforms = waveforms.to(device)
        labels = labels.to(device)

        # Extract mel-spectrograms
        with torch.no_grad():
            # Process batch
            batch_mels = []
            for wav in waveforms:
                mel = feature_extractor.extract_mel_spectrogram(wav)
                batch_mels.append(mel)
            mels = torch.stack(batch_mels)

        # Forward
        optimizer.zero_grad()
        outputs = model(mels)
        loss = criterion(outputs, labels)

        # Backward
        loss.backward()
        optimizer.step()

        # Stats
        total_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

        pbar.set_postfix({"loss": loss.item(), "acc": 100.0 * correct / total})

    return {
        "loss": total_loss / len(dataloader),
        "accuracy": 100.0 * correct / total,
    }


def validate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: str,
    feature_extractor: FeatureExtractor,
) -> Dict[str, float]:
    """Validate model."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for waveforms, labels in tqdm(dataloader, desc="Validation"):
            waveforms = waveforms.to(device)
            labels = labels.to(device)

            # Extract features
            batch_mels = []
            for wav in waveforms:
                mel = feature_extractor.extract_mel_spectrogram(wav)
                batch_mels.append(mel)
            mels = torch.stack(batch_mels)

            outputs = model(mels)
            loss = criterion(outputs, labels)

            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    return {
        "loss": total_loss / len(dataloader),
        "accuracy": 100.0 * correct / total,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/detector.yaml")
    parser.add_argument("--output-dir", type=str, default="runs/detector")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Setup
    device = args.device
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save config
    with open(output_dir / "config.yaml", "w") as f:
        yaml.dump(config, f)

    # Initialize model
    model_type = config["model"].get("type", "light")
    if model_type == "light":
        model = LightDetector(
            input_dim=config["model"].get("input_dim", 80),
            embedding_dim=config["model"].get("embedding_dim", 128),
        )
    else:
        model = DeepfakeDetector(
            input_dim=config["model"].get("input_dim", 80),
            embedding_dim=config["model"].get("embedding_dim", 256),
            dropout=config["model"].get("dropout", 0.5),
        )

    model = model.to(device)

    # Feature extractor
    feature_extractor = FeatureExtractor(
        sample_rate=config["data"].get("sample_rate", 16000),
        device=device,
    )

    # Datasets
    train_dataset = AudioDataset(
        manifest_path=config["data"]["train_manifest"],
        sample_rate=config["data"]["sample_rate"],
        max_duration=config["data"].get("max_duration", 10.0),
        augment=config["data"].get("augmentations", {}),
    )

    val_dataset = AudioDataset(
        manifest_path=config["data"]["val_manifest"],
        sample_rate=config["data"]["sample_rate"],
        max_duration=config["data"].get("max_duration", 10.0),
        augment=False,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=config["data"]["batch_size"],
        shuffle=True,
        num_workers=config["data"].get("num_workers", 4),
        collate_fn=collate_fn,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config["data"]["batch_size"],
        shuffle=False,
        num_workers=config["data"].get("num_workers", 4),
        collate_fn=collate_fn,
    )

    # Optimizer and scheduler
    optimizer = optim.AdamW(
        model.parameters(),
        lr=config["training"]["lr"],
        weight_decay=config["training"].get("weight_decay", 0.0001),
    )

    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=config["training"]["epochs"],
    )

    # Loss
    criterion = nn.CrossEntropyLoss(
        label_smoothing=config["loss"].get("label_smoothing", 0.1)
    )

    # Tensorboard
    writer = SummaryWriter(output_dir / "logs")

    # Training loop
    best_val_acc = 0.0
    epochs = config["training"]["epochs"]

    for epoch in range(1, epochs + 1):
        print(f"\nEpoch {epoch}/{epochs}")

        # Train
        train_metrics = train_epoch(
            model, train_loader, optimizer, criterion, device, feature_extractor, epoch
        )

        # Validate
        val_metrics = validate(model, val_loader, criterion, device, feature_extractor)

        # Scheduler step
        scheduler.step()

        # Log
        print(f"Train Loss: {train_metrics['loss']:.4f}, Acc: {train_metrics['accuracy']:.2f}%")
        print(f"Val Loss: {val_metrics['loss']:.4f}, Acc: {val_metrics['accuracy']:.2f}%")

        writer.add_scalar("train/loss", train_metrics["loss"], epoch)
        writer.add_scalar("train/accuracy", train_metrics["accuracy"], epoch)
        writer.add_scalar("val/loss", val_metrics["loss"], epoch)
        writer.add_scalar("val/accuracy", val_metrics["accuracy"], epoch)

        # Save checkpoint
        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            torch.save({
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "val_accuracy": val_metrics["accuracy"],
            }, output_dir / "best_model.pth")
            print(f"Saved best model with accuracy: {best_val_acc:.2f}%")

        # Regular checkpoint
        if epoch % config["logging"].get("save_every", 5) == 0:
            torch.save({
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
            }, output_dir / f"checkpoint_epoch_{epoch}.pth")

    print(f"\nTraining complete. Best validation accuracy: {best_val_acc:.2f}%")
    writer.close()


if __name__ == "__main__":
    main()
