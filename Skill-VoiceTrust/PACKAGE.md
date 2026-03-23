# Skill-VoiceTrust package notes

This directory is intended to be copied directly into an OpenClaw skills directory.

Contents:
- `SKILL.md` — the VoiceTrust skill
- `references/quickstart.md` — first-time setup notes
- `scripts/demo.py` — CLI entry for VoiceTrust runtime
- `runtime/` — minimal VoiceTrust runtime bundle

Recommended use:
1. Copy `Skill-VoiceTrust/` into your OpenClaw skills directory.
2. Place or unpack `runtime/` into a local VoiceTrust runtime directory.
3. Create a local Python environment for that runtime.
4. Enroll the owner profile.
5. Register your machine-specific voice-message handling convention in `TOOLS.md`.

This package does not define one universal STT backend.
Use your own local STT path and pair it with VoiceTrust in your local voice-message protocol.
