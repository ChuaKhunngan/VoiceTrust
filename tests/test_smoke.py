"""Smoke tests for the promoted local VoiceTrust mainline."""
from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parent.parent


def _extract_json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    assert start != -1 and end != -1 and end > start, text
    return json.loads(text[start:end + 1])


def test_demo_json_smoke():
    audio = ROOT / "tests" / "fixtures" / "test_audio.wav"
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

    payload = _extract_json_object(result.stdout)
    assert "overall_trust" in payload
    assert "speaker_match" in payload
    assert "speech_duration" in payload
    assert "speech_ratio" in payload
    assert "vad_status" in payload
