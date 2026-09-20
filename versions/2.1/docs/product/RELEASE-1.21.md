# Tracer 1.21 — Finishing & Publishing Release

Direction: A unified editing product where Paper Edit and Storyline are two synchronized views of the same sequence, with Premiere-style timeline tools and complete data preservation.

## Delivered Journeys

- **One Sequence, Two Views**:
  - Paper Edit owns the spoken-story spine (transcript text, passage order, inclusion/exclusion, speech in/out points).
  - Storyline owns the complete audiovisual assembly (dialogue clips, B-roll on V2, additional audio on A2, track controls, fine timeline edits).
  - Stable `passage_id` identity connects manuscript paragraphs directly to timeline clips.
- **Bi-Directional Diff Synchronization**:
  - Reordering, deleting, or restoring passages in Paper Edit automatically ripples spoken clips on the timeline while keeping all B-roll and Storyline-only layers intact.
  - Trimming linked spoken clips in Storyline updates passage in/out timestamps in Paper Edit and marks them as manual adjustments.
- **Timeline-Aware Manuscript UI**:
  - Quiet gutter badges reveal on hover/focus with exact start–end timecodes, duration, and timing quality.
  - Quick action buttons: Play Source, Trim In/Out with preview and reset, and Split Passage at caret.
  - Dynamic sync status indicator: `Synced to Storyline · X passages · MM:SS`.
- **Storyline 6-Tool Visual Dock**:
  - Selection (`V`): Select and move clips, scrub ruler.
  - Track Select Forward (`A`): Click to select all clips to the right (Shift for all tracks).
  - Ripple Edit (`B`): Drag clip edges to trim while live-rippling downstream edits without gaps.
  - Razor (`C`): Split clip at pointer with real-time hover guide line.
  - Hand (`H`): Click and drag to pan viewport.
  - Zoom (`Z`): Click to zoom in; Alt/Ctrl+click to zoom out.
- **Premiere Keyboard Shortcuts with Text Guard**:
  - `Space` for playback, `Left`/`Right` for frame stepping, `Up`/`Down` for edit boundary jumps.
  - `Ctrl+K` for split at playhead, `Delete` for standard delete, `Shift+Delete` for ripple delete.
  - Application-level focus guard prevents tool shortcuts from firing while typing in search bars or text fields.
- **Hygiene & Diagnostics**:
  - Schema version 121 with automated migration from 1.19.2 and 1.20.
  - Rotating local diagnostic logger (`tracer.log`) with user path sanitization.
  - Automated verification runner (`verify_121.py`) with 10 visual screenshots covering wide and narrow viewports.

## Verification & Status

- 60 automated tests pass (52 existing baseline tests + 8 new 1.21 tests in `tests/test_release121.py`).
- Isolated UI verification passes across Queue, Library, Collection, Paper Edit, Storyline, Transcape, and Empty states at 1440×900 and 1100×720 viewports.
- All screenshots saved in `verification/1.21/`.
