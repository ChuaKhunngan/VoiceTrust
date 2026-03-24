#!/usr/bin/env python3
"""Ensure local VoiceTrust model assets are present.

This script keeps the distributed skill bundle lightweight:
- the ClawHub package contains code + setup logic
- large SpeechBrain model checkpoints are downloaded on demand

Default behavior:
- check whether required local model files exist
- download missing files from the official GitHub raw directory
- report exact status in human or JSON form
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = PACKAGE_ROOT / "runtime"
MODEL_DIR = RUNTIME_ROOT / "assets" / "models" / "ecapa_voxceleb"
RAW_BASE_URL = (
    "https://raw.githubusercontent.com/ChuaKhunngan/VoiceTrust/main/"
    "assets/models/ecapa_voxceleb"
)

REQUIRED_FILES = [
    "hyperparams.yaml",
    "classifier.ckpt",
    "embedding_model.ckpt",
    "label_encoder.ckpt",
    "mean_var_norm_emb.ckpt",
]


def file_report() -> dict:
    report = {}
    for name in REQUIRED_FILES:
        path = MODEL_DIR / name
        report[name] = {
            "present": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "path": str(path),
            "url": f"{RAW_BASE_URL}/{name}",
        }
    return report


def missing_files() -> list[str]:
    return [name for name in REQUIRED_FILES if not (MODEL_DIR / name).exists()]


def download_file(name: str, force: bool = False) -> dict:
    target = MODEL_DIR / name
    url = f"{RAW_BASE_URL}/{name}"
    if target.exists() and not force:
        return {
            "file": name,
            "status": "skipped",
            "path": str(target),
            "size_bytes": target.stat().st_size,
            "url": url,
        }

    tmp = target.with_suffix(target.suffix + ".part")
    try:
        with urllib.request.urlopen(url) as response, tmp.open("wb") as fh:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
        tmp.replace(target)
        return {
            "file": name,
            "status": "downloaded",
            "path": str(target),
            "size_bytes": target.stat().st_size,
            "url": url,
        }
    except (HTTPError, URLError) as e:
        if tmp.exists():
            tmp.unlink()
        return {
            "file": name,
            "status": "error",
            "path": str(target),
            "url": url,
            "error": str(e),
        }


def ensure_models(force: bool = False) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    before_missing = missing_files()
    actions = []

    for name in REQUIRED_FILES:
        if force or name in before_missing:
            actions.append(download_file(name, force=force))

    after_missing = missing_files()
    return {
        "ok": not after_missing,
        "model_dir": str(MODEL_DIR),
        "raw_base_url": RAW_BASE_URL,
        "missing_before": before_missing,
        "missing_after": after_missing,
        "actions": actions,
        "files": file_report(),
    }


def print_human_status(result: dict) -> int:
    if result["ok"]:
        print(f"VoiceTrust model assets ready: {result['model_dir']}")
        if result["actions"]:
            print("Downloaded/checked files:")
            for action in result["actions"]:
                status = action["status"]
                print(f"  - {action['file']}: {status}")
        return 0

    print("VoiceTrust model assets are incomplete.")
    print(f"Model dir: {result['model_dir']}")
    print(f"Source: {result['raw_base_url']}")
    print("Missing files after ensure:")
    for name in result["missing_after"]:
        print(f"  - {name}")
    errors = [a for a in result["actions"] if a.get("status") == "error"]
    if errors:
        print()
        print("Download errors:")
        for action in errors:
            print(f"  - {action['file']}: {action['error']}")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure local VoiceTrust model assets exist")
    parser.add_argument("--json", action="store_true", help="Output machine-readable status")
    parser.add_argument("--check-only", action="store_true", help="Only report status; do not download")
    parser.add_argument("--force", action="store_true", help="Re-download all required files")
    args = parser.parse_args()

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    if args.check_only:
        result = {
            "ok": not missing_files(),
            "model_dir": str(MODEL_DIR),
            "raw_base_url": RAW_BASE_URL,
            "missing": missing_files(),
            "files": file_report(),
        }
        if args.json:
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 2
        if result["ok"]:
            print(f"VoiceTrust model assets ready: {result['model_dir']}")
            return 0
        print("VoiceTrust model assets are missing.")
        print(f"Model dir: {result['model_dir']}")
        for name in result["missing"]:
            print(f"  - {name}")
        return 2

    result = ensure_models(force=args.force)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2
    return print_human_status(result)


if __name__ == "__main__":
    sys.exit(main())
