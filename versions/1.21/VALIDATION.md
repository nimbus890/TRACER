# Tracer 1.20 verification — 17 September 2026

Current result: **52 automated tests pass**, and `python verify_120.py` exits
successfully after isolated UI journey checks. `python verify.py ui` now uses
the current verifier. No user media or saved library is used by these checks.

Verified Library/Collection separation, adding selected footage, manuscript
replacement/deletion/undo, shared sequence identity, preview playhead linkage,
Cut-tool splits and undo, migration/reload, collision-safe original-file export,
missing-source reporting, and transcript/visual evidence in Transcape.

Rendered desktop 1440×900 and narrow 1100×720 screenshots under
`verification/1.20/`, including offline and empty states. The manuscript remains
passage-timed; manual Storyline changes are preserved as a separate cut if a
later manuscript edit rebuilds its linked sequence. Transcape is a bounded local
overview (up to 90 files), not a new semantic inference engine.

This release is a runnable source snapshot. GPU inference, a fresh installer,
and import in an installed Premiere application were not tested in this pass.
Full scope: `docs/product/RELEASE-1.20.md`.

## Historical 1.15 verification — 16 September 2026

## Passed

- 30 automated tests covering the full processing/batch baseline plus Paper Edit persistence, selection order, transcript analysis, package export, native multi-file import, multi-video Library selection, linked timeline edits, infinite overlap stacking, Premiere XML, and collected-media behavior.
- A real Paper Edit trim from generated verification footage retained video, audio, 10 fps, and the requested 1.0 second duration within probe tolerance.
- Paper Edit was rendered offscreen in Tracer's dark neutral/orange palette with editable transcript rows, speaker/timecode fields, amber key-line marker, red margin note, freehand pen layer, source preview, visual references, and draggable paper sequence.
- Storyline was checked with Library insertion, linked A/V creation, automatic new-layer creation for an overlapping drop, protected edits on locked linked tracks, compact Delivery drawer, and narrow 1100×720 rendering.
- Queue was checked with the native Windows multi-file path, Explorer drag-and-drop support for folders/files, selection behavior, sharp opaque delete glyph, and local resource meters.
- Video Library retained the 1.14 behavior: direct/embedded hit counts, highlighted matches, persistent results rail while changing videos, outside-click collapse, reflowed transcript/preview/gallery, icon arrows, and exact Explorer reveal.
- Processing options retained exact intervals, output-only mode combinations, advanced settings, JPEG/PNG behavior, and disabled-state clarity.
- High-DPI setup now requests per-monitor v2 awareness on Windows, pass-through Qt scaling, and 2× vector-drawn UI glyphs.
- Fresh captures were generated at **verification/paper-edit.png**, **queue.png**, **projects.png**, **projects-delivery.png**, **projects-narrow.png**, **projects-empty.png**, **library.png**, **library-drawer.png**, **options.png**, **options-advanced.png**, **options-disabled.png**, and **settings.png**.

The processing engine remains on the previously GPU-verified baseline. GPU transcription was not rerun for this interface/editor release. No 1.15 standalone executable or installer was built.

## Limits of verification

Optional larger models were not downloaded or benchmarked. The UI run used Qt's offscreen platform, while the native picker itself is covered through its call path and should receive final interaction testing in a normal Windows session. Transcript accuracy is demonstrated on generated English speech and is not guaranteed for every recording. The installer remains unsigned when built.

## Earlier baselines

- 1.14: 25 tests plus the adaptive Library, resource meters, project/timeline tools, Premiere XML, and collected-media delivery.
- 1.13: 19 tests covering unified imports, Explorer reveal, icon updates, and transcript highlighting.
- 1.12: 15 core processing tests plus real NVIDIA GPU and packaged-executable processing verification.
