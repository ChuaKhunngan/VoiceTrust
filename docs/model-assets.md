# Model Assets

## Current runtime policy

VoiceTrust no longer relies on Hugging Face as a runtime dependency for its main speaker verification path.

Current mainline model assets live inside the project at:

- `assets/models/ecapa_voxceleb/`

This directory contains the local SpeechBrain 1.0.3-compatible ECAPA speaker verification assets used by VoiceTrust.

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

## Current mainline scope

The local model assets currently support:
- speaker verification / recognition

They do not currently bundle:
- anti-spoofing
- language ID

Those should only be added later when local project-owned assets are truly available.
