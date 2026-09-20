# Tracer 1.22 verification — 18 September 2026

Current result: **66 automated tests pass** with one existing environment-dependent skip. `verify_122.py` completes successfully using isolated fixture state; it does not read or modify the user's media library.

Verified behavior includes:

- immediate manuscript persistence with debounced linked-sequence synchronization;
- stable passage and clip identity across repeated Paper Edit synchronization;
- preservation of Storyline-only tracks;
- sequence-ID-based Storyline-to-Paper trim resolution;
- passage exclude and restore from the existing Passage Order panel;
- symbol-led Storyline controls and guarded shortcuts;
- linked/locked Ripple behavior and undo integration;
- Library/Collection separation and collection actions;
- synchronized Storyline playhead/preview controls;
- wide 1440×900 and narrow 1100×720 layouts;
- offline and empty states plus the Transcape entry surface.

Screenshots are stored under `verification/1.22/`.

The final Windows standalone build completes successfully at `dist/Tracer/Tracer.exe`. It contains the packaged `VERSION` value `1.22`, includes the local Tiny transcription and visual-index models, and remained running during an isolated startup smoke test before the test process was closed. The executable SHA-256 is `45BED9AF4E93A4AA5E4E2029B6801CC671BD86DD937C3CA76CEC3A51E5B03A8D`.

The PyInstaller warning report contains optional platform, converter, training, and ONNX authoring modules that Tracer does not call at runtime; no missing Tracer module was reported. The final standalone directory is about 2.47 GB because it includes the local inference runtimes and models.

The processing engine remains on the previously verified baseline. Native GPU transcription, an installed Premiere import, clean-machine installer behavior, and code signing were not exercised by the isolated UI verifier. Inno Setup is not installed on this workstation, so `Tracer-Setup-1.22.0.exe` was not generated here; `Tracer.iss` is updated and ready for that release-machine step.

Full scope: `docs/product/RELEASE-1.22.md`.
