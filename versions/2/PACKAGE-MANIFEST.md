# Tracer 2 package manifest

## Provenance

- Source baseline: `versions/1.23`, including changes produced through multiple development applications.
- Portable rollback baseline: the complete `versions/1.23/dist/Tracer` package.
- Version 2 source identifier: `2.0.0`.
- Portable baseline identifier: `1.23` until the first version 2 rebuild.

No unfamiliar source file was discarded or rewritten during the copy. Generated Python caches and old PyInstaller work files were intentionally excluded.

## Included for offline/self-contained operation

- Application source, assets, documentation, tests, release tooling, and verification artifacts.
- Portable executable and all bundled Python, Qt, media, GPU, inference, and native runtime dependencies.
- Tiny and Base transcription models.
- Visual Index model and its license/support files.
- Current library state and processing analytics.
- Third-party notices and collected dependency licenses.

## Intentionally excluded

- Python bytecode caches and model download caches; neither is required at runtime.
- Previous removed-model backups, transient logs, and stale lock files.
- Original source videos and generated result folders. The library keeps their existing paths; media remains user-owned and external by design.
- The repository `.venv`. The portable runtime does not require it. Source development still uses a developer Python environment when rebuilding.

## Data boundaries

The portable app reads and writes `portable/Tracer/data`. The editable source reads and writes `source/data`. Each contains its own model and state copy, so neither mode depends on `C:\projects\TransPro\data`.

Because the two data copies are deliberately independent, changes made while running the portable build do not automatically update the source-development state, and vice versa.
