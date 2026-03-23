# Model Assets

## Current runtime policy

VoiceTrust no longer relies on Hugging Face as a runtime dependency for its main speaker verification path.

Current mainline model assets live inside the project at:

- `assets/models/ecapa_voxceleb/`

This directory currently contains the local SpeechBrain 1.0.3-compatible ECAPA speaker verification assets used by VoiceTrust.

## Included local assets

Expected files:
- `hyperparams.yaml`
- `embedding_model.ckpt`
- `classifier.ckpt`
- `mean_var_norm_emb.ckpt`
- `label_encoder.ckpt`

## Why this exists

Reasons for local asset packaging:
- reproducible local runs
- reproducible open-source onboarding
- no runtime dependence on remote model registries
- reduced risk from upstream hosted repo churn

## Current limitation

Only the main speaker verification path is local-asset based right now.
Anti-spoofing remains disabled until local project-owned model assets are prepared for that task as well.

## Future direction

If additional SpeechBrain-backed capabilities are added (for example LID), their runtime assets should also be brought under local project control rather than fetched dynamically at runtime.
