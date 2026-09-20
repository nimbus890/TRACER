# Tracer 2

This folder is the self-contained starting point for the Tracer 2 major-version line.

## Run the stable baseline

Double-click `Run Tracer.cmd`. The packaged application, Python/Qt runtime, native libraries, active models, and copied workspace state live under `portable/Tracer`; no repository-level Python environment is required.

The executable is the last proven 1.23 build copied without altering its internals. It is retained as the rollback/reference runtime while version 2 development begins.

## Folder layout

- `source/` — editable version 2 source initialized from the complete 1.23 snapshot.
- `source/data/` — local development state and active models, so source runs do not use the repository-level data folder.
- `portable/Tracer/` — standalone 1.23 baseline, bundled dependencies, licenses, models, and copied workspace state.
- `.build/` — generated only when `source/build.py` is run; safe to recreate.
- `PACKAGE-MANIFEST.md` — provenance, inclusion rules, and portability notes.

## Build version 2

Run `source/build.py` from the project Python environment. Its output is intentionally directed to `portable/Tracer`, while temporary build files stay in `.build`.

Do not edit the portable runtime by hand. Make changes in `source/`, test there, and rebuild.
