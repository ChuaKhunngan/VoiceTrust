"""Smoke tests for the promoted local VoiceTrust mainline."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def test_demo_json_smoke():
    audio = ROOT / "remote-import" / "snapshot_20260322" / "test_audio.wav"
    assert audio.exists(), f"Missing test audio: {audio}"

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "demo.py"),
        "--audio",
        str(audio),
        "--speaker",
        "owner",
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    assert "overall_trust" in result.stdout
    assert "speaker_match" in result.stdout
