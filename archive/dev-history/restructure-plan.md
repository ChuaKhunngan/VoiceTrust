# Restructure Plan

## Goal

Restructure `projects/voicetrust/` into a maintainable, open-source-ready project **without over-modifying working imported code**.

## Principles

1. preserve imported working code
2. add structure before large code changes
3. make the public story clear
4. separate current mainline from historical residue gradually
5. keep OpenClaw integration as the product north star

## Phase 1 — Structure and documentation

- [x] Add top-level `README.md`
- [x] Add `BLUEPRINT.md`
- [x] Add `LICENSE`
- [x] Add `.gitignore`
- [x] Add `pyproject.toml`
- [x] Add import provenance notes
- [ ] Add open-source readiness checklist
- [ ] Add integration contract draft

## Phase 2 — Mainline clarification

- [ ] Identify which imported modules are current-path
- [ ] Identify which imported modules are legacy/reference only
- [ ] Mark anti-spoofing limitations explicitly
- [ ] Define minimal supported runtime path

## Phase 3 — Code promotion

- [x] Promote selected runtime modules into a clean local project root layout (`src/`, `scripts/`, `configs/`, `tests/`, `data/voiceprints/`)
- [x] Keep imported snapshot intact until promoted path is stable
- [x] Add minimal smoke tests
- [x] Add example commands for enrollment and verification

## Phase 4 — Open-source polish

- [ ] Confirm license choice and attribution details
- [ ] Replace placeholder repository URLs
- [ ] Review dependency footprint
- [ ] Add contributor-facing setup instructions
- [ ] Add limitations / threat-model section

## Anti-goals

Do not do these too early:
- rewrite algorithms for elegance
- move every imported file immediately
- present anti-spoofing as production-grade before validation
- rebuild the whole project before integration needs are fixed
