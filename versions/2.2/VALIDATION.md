# Tracer 1.23 verification — 18 September 2026

Current result: **73 automated tests pass** with one existing environment-dependent skip (total 74 tests). `verify_123.py` and `verify.py ui` complete successfully using isolated fixture state; they do not read or modify the user's media library.

Verified behavior includes:

- beta feature toggle positioned immediately beside the beta flask icon; defaults off, persists across sessions;
- beta-off hides Paper Edit and Visual Indexing throughout the app; library picker subtitle adjusted;
- double-clicking either the Tracer icon or wordmark opens Transcape;
- Transcape rebuilt with force-directed physics, cluster seeding, node dragging, cursor repulsion, proximity labels, middle-mouse panning, wheel zoom, spatial reveal, and frameless HUD chrome;
- Storyline Sequence Media uses a Select Collection dropdown, collection thumbnails, and a bottom-right List/Grid toggle switch that reorganizes media dynamically;
- Storyline per-track hide/mute and lock vector controls directly on each track header with click toggling;
- Storyline toolbar with edit tools on the left and Snap, Fit complete sequence, and Zoom slider right-aligned;
- timeline shortcuts: Delete, Shift+Delete (ripple), Ctrl+K (split), Ctrl+Y (redo), Ctrl+Shift+Z (redo), Ctrl+Z (undo), clipboard, Space play/pause;
- Paper Edit restyled as a clean document-like sheet centered in its scroll area;
- library video preview separated from transcript/frames/details with a resizable splitter;
- processing overlay redesigned with translucent scrim backdrop (`rgba(8, 10, 12, 195)`), opaque card `#141414`, reliable outside-click dismissal, and cursor glow;
- Transcape-formula cursor aura strictly confined inside the left menu bar (and overlay card) without viewport leakage;
- wide 1440×900 and narrow 1100×720 layouts;
- offline and empty states plus the Transcape entry surface.

Screenshots are stored under `verification/1.23/`.

The final Windows standalone build completes successfully at `dist/Tracer/Tracer.exe`. It contains the packaged `VERSION` value `1.23`, includes the local Tiny transcription and visual-index models, and bundles licenses and assets. The executable SHA-256 is `6AAA94A0BE1EBB7CA67D92738E2864CF6C5C9448FD52CAAF653FA22EBCBEBC7A`.

The PyInstaller report confirms all necessary modules collected (`faster_whisper`, `ctranslate2`, `av`, `onnxruntime`, `tokenizers`, `huggingface_hub`, etc.). The final standalone directory is about 2.41 GB because it includes the local inference runtimes and models.

The processing engine remains on the previously verified baseline. Native GPU transcription, an installed Premiere import, clean-machine installer behavior, and code signing were not exercised by the isolated UI verifier. Inno Setup is not installed on this workstation, so `Tracer-Setup-1.23.0.exe` was not generated here; `Tracer.iss` is updated to 1.23.0 and ready for that release-machine step.

Full scope: `docs/product/RELEASE-1.23.md`.
