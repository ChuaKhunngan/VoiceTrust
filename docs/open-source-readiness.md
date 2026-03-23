# Open-Source Readiness

This document tracks what remains before VoiceTrust is comfortable to publish as an open-source project.

## Already in place

- public-facing top-level README exists
- architecture / intent blueprint exists
- project-local license file exists
- basic packaging metadata exists
- imported snapshot provenance is documented
- project roadmap already describes MVP direction

## Still needed

### Product clarity
- [ ] concise threat model
- [ ] explicit statement that trust score is not sole high-risk auth
- [ ] precise OpenClaw integration contract

### Codebase clarity
- [ ] identify supported mainline modules
- [ ] identify legacy/training-era residue
- [ ] remove ambiguity around recommended entrypoints

### Packaging
- [ ] verify `pyproject.toml` against actual promoted package layout
- [ ] decide whether to keep `requirements.txt` in parallel
- [ ] define example install commands for users

### Testing
- [ ] smoke test for enrollment flow
- [ ] smoke test for verification flow
- [ ] smoke test for JSON output schema

### Release hygiene
- [ ] replace placeholder GitHub URLs
- [ ] add changelog or release notes policy
- [ ] review third-party attribution / model-license notes
- [ ] decide whether sample audio will be shipped

### Documentation
- [ ] contributor setup guide
- [ ] limitations section
- [ ] runtime data / privacy note for voiceprints
- [ ] examples for single-owner enrollment workflow

## Publication bar

A reasonable first public release should meet these minimum expectations:
- someone can understand what the project does
- someone can install it without guessing too much
- someone can run the basic flow
- limitations are stated honestly
- historical imported code does not confuse the main product story
