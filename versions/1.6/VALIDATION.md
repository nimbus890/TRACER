# TransPro 1.6 verification — 12 September 2026

## Passed

- 15 automated tests for folder ordering, selected-file filtering, overlapping-folder deduplication, continuing after a failed video, cancellation before the next video, cancellation while paused, stopping concurrent processing on failure, timestamped JPEG and lossless PNG extraction, scene cuts, transcript exports, reuse validation, changed-source invalidation, recursive scanning, unreadable media, size estimation, transcription-only output, and privacy-conscious local processing analytics.
- Real GPU processing of a generated 15-second spoken video on an NVIDIA GeForce RTX 4050 Laptop GPU (6 GB).
- Combined mode: 31 timestamped JPEG screenshots plus TXT, SRT, VTT, JSON transcripts.
- Transcription-only mode: transcript exports, zero images, no screenshots directory.
- The same combined and transcription-only checks passed in the standalone executable, using its bundled libraries and Tiny model.
- Offline NanoDet visual indexing and the video-first footage-search interface were checked, including saved keywords and lazy five-second detail frames.
- Offscreen interface checks and visual inspection of the folder queue, scroll-free single-column processing dialog, collapsible Advanced settings, projects, footage search, redesigned results library and model settings. The smaller opaque icon tiles, active compact Start action, one-line job estimate, recommendation-marked sliders, related-setting fade states, JPEG/PNG state, Automatic/Custom language state, AI sampling control, 1280 px Standard screenshot default, direct source/results folder actions, collapsing video browser, draggable transcript/preview divider, icon playback control, folder selection, and an exact 0.15-second interval were checked.

Reports and generated sample media are in `verification`. The earlier executable report is `verification/packaged-verification.json`; no 1.6 executable was built. Screenshots of the UI include `verification/queue.png`, `options.png`, `options-advanced.png`, `library.png`, and `settings.png`.

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
