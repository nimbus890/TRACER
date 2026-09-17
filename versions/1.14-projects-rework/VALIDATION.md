# Tracer 1.14 verification — 14 September 2026

## Passed

- 25 automated tests, including the complete processing and batch suite plus 1.14 direct/embedded query classification, sequence migration, linked-edit synchronization and lock detection, atomic Premiere XML generation, offline-source detection, portable collected-media XML, and filename-collision coverage.
- Offscreen interface verification of Folder Queue, Project Editing Room, adaptive Video Library search, processing options, and Settings.
- Folder Queue has one direct Add media action with no source-type menu. The picker accepts folders, supported videos, or both, while ignoring unsupported and missing paths.
- The queue removal glyph remains sharp white even when unavailable, uses an opaque bordered button surface, and changes to danger red on hover.
- Video Library keeps search results open while moving between videos, reports direct and embedded hit counts per video, uses distinct transcript highlighting, reflows the transcript/preview/gallery around its resizable rail, and collapses the rail on an outside click.
- Projects provides tabbed multitrack sequences, linked video/audio insertion, source/transcript inspection, clip editing and undo/redo, markers, track controls, zoom/fit, an export queue, Premiere-compatible XML, offline-media preflight/relink, and portable collected-media delivery.
- The Upgrade Pass keeps linked A/V clips synchronized during drag edits, applies track locks to destructive linked edits, replaces unsupported source-monitor text glyphs with rendered icons, adds standard editing shortcuts and tooltips, disables empty-timeline delivery actions, reports partial collections accurately, and writes timeline XML atomically.
- The Project Editing Room was rerendered and checked at both 1280×860 and a narrower 1100×720 desktop viewport; the compact timeline toolbars remain legible at both sizes. The narrow capture is `verification/projects-narrow.png`.
- The Projects workspace rework was checked in empty, active-editing, narrow, and delivery-open states. Project media now has one picker and one draggable tree instead of separate Folder/Video actions plus a duplicate drag list; empty projects show focused onboarding; Transcript is no longer mislabeled as Notes; and Delivery is collapsed until requested. Captures are `verification/projects-empty.png`, `verification/projects.png`, `verification/projects-narrow.png`, and `verification/projects-delivery.png`.
- The 92 px navigation rail uses symbols plus small labels. Tiny local GPU, VRAM, and RAM readouts use `Tracer / system` percentages and fall back to em dashes when unavailable.
- Fresh screenshots were rendered to `verification/queue.png`, `verification/library.png`, `verification/library-drawer.png`, `verification/options.png`, `verification/options-advanced.png`, `verification/options-disabled.png`, `verification/projects.png`, and `verification/settings.png`.
- The processing engine is unchanged from the GPU-verified baseline; GPU transcription was not rerun for this UI-focused release. The resource sampler returned live GPU, VRAM, and RAM percentages on the verification machine.

No 1.14 standalone executable or installer was built.

## Earlier Tracer 1.13 verification — 13 September 2026

- 19 automated tests passed for the 1.13 unified media picker, exact Explorer reveal, icon updates, transcript highlighting, and the complete earlier processing/batch suite.
- The preserved source is under `versions/1.13`; no 1.13 executable or installer was built.

## Earlier Tracer 1.12 verification — 12 September 2026

## Passed

- 15 automated tests for folder ordering, selected-file filtering, overlapping-folder deduplication, continuing after a failed video, cancellation before the next video, cancellation while paused, stopping concurrent processing on failure, timestamped JPEG and lossless PNG extraction, scene cuts, transcript exports, reuse validation, changed-source invalidation, recursive scanning, unreadable media, size estimation, transcription-only output, and privacy-conscious local processing analytics.
- Real GPU processing of a generated 15-second spoken video on an NVIDIA GeForce RTX 4050 Laptop GPU (6 GB).
- Combined mode: 31 timestamped JPEG screenshots plus TXT, SRT, VTT, JSON transcripts.
- Transcription-only mode: transcript exports, zero images, no screenshots directory.
- The same combined and transcription-only checks passed in the standalone executable, using its bundled libraries and Tiny model.
- Offline NanoDet visual indexing and the video-first search flow inside Video Library were checked, including icon-only Audio/Visual scopes, always-searchable source names, depth filtering, saved keywords and lazy five-second detail frames.
- Offscreen interface checks and visual inspection of the folder queue, fully opaque frameless processing surface, lightly blurred surrounding background, gear-only side-expanding Advanced settings, projects, unified Video Library and compact model settings. The small opaque output controls use one-step lighter tints of taskbar-style blue, yellow and green with black symbols; the restored data-network-plus-search icon, centered icon-only red cancel action, right-aligned compact Start action, single Capture/Scene Change row, joined JPEG/PNG control on the Image Quality row, demarcated Save Results area, one-line job estimate, recommendation-marked sliders, related-setting fade states, Automatic/Custom language state, AI sampling control, 1280 px Standard screenshot default, direct source/results folder actions, filename page heading, See All/list arrows, collapsing video browser, draggable transcript/preview divider, icon playback control, folder selection, and an exact 0.15-second interval were checked.
- Settings presents all Whisper downloads in one compact readable row. The separate Footage Search navigation/page is absent, leaving four main navigation items. The See All drawer overlays the workspace from its left edge instead of changing the dashboard width.
- Folder Queue uses a compact trash icon beside the Add media menu. The menu exposes native Windows folder selection and native multi-video selection; newly added groups expand for immediate per-video selection. Removing a selected child removes only that queue entry and never deletes source media.

Reports and generated sample media are in `verification`. The earlier executable report is `verification/packaged-verification.json`; no 1.12 executable was built. Screenshots of the UI include `verification/queue.png`, `options.png`, `options-advanced.png`, `library.png`, `library-drawer.png`, and `settings.png`.

The initial packaged executable contained an incompatible ICU library picked up from an unrelated Poppler installation on the development machine. The build now restricts its dependency search path, and the corrected executable passed the GPU checks.

## Limits of verification

Optional larger models have not been downloaded or benchmarked. The GPU was verified on this Windows 11 machine, not across other GPU/driver combinations. The installer is built from the verified standalone app; it is unsigned. Transcript accuracy is demonstrated on generated English speech, not guaranteed for every language or recording. Scene detection is an abrupt visual-change heuristic.

## Slate copy

All three versions were copied from Dice Red into `C:\projects\Slate`, keeping their originals intact. Source and destination file counts and total byte sizes matched:

| Folder | Files | Bytes |
| --- | ---: | ---: |
| slate v0.3 | 449 | 183,490,773 |
| slate v2 | 321 | 152,775,145 |
| slate v3.1 | 42 | 93,802,670 |

These are copies of the existing apps; their behavior and external dependencies were not changed.
