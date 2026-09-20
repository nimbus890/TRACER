# Tracer Changelog

All notable changes to Tracer are documented here. Versions follow the existing snapshot numbering.

---

## 2.3 — Non-Blocking Async Export, Clean Checkbox Restyling & Unified Media Ingestion

- **Non-Blocking "Export as Project" Overlay**:
  - Eliminated Windows "(Not Responding)" lockups by shifting high-volume video collection copying into an asynchronous `ExportWorker` thread with 4MB chunked streaming and byte-level progress reporting.
  - Implemented `ExportProjectDialog` with a folder destination picker, live 0–100% progress bar, status text, click-outside dismissal, backdrop blur (`QGraphicsBlurEffect`), darkened semi-transparent background, and outer radial cursor aura glow.
  - Connected seamlessly across Collections ("Export as Project", "Export Selected Files", context menu), Timeline (`collect_media`), and Paper Edit (`export_script`).
- **Clean v1.23 Checkbox Restoration & Centering**:
  - Removed orange, rounded/boxy indicator overrides; restored the clean, subtle dark Fusion checkbox aesthetic from v1.23.
  - Fixed squished indicator proportions by removing conflicting vertical min-height and padding.
  - Horizontally and vertically centered the checkbox inside the Library media table gap (`MediaTableDelegate.paint`) with crisp 1:1 box geometry and sharp checkmark rendering.
  - Preserved enlarged click hitboxes across the entire column cell and queue list items for effortless toggling.
- **Universal Add Media File Picker**:
  - Replaced the single-mode Windows file dialog with `MediaPickerDialog`, allowing simultaneous selection of both folders and individual video files in the same view.
  - Added an "Add this folder" action button and recursive folder discovery.

---

## 2.1 — Refined Playback, Workspace Polish & Sequence Preview Unification

- **Unified Video Player Controls & Captions**:
  - Modern media control bar matching the Tracer 2.1 design specification: Play/Pause, monospace current/duration timecode (`00:12:14 / 00:42:18`), accent orange scrubber bar (`#ff7a1a`) with circular handle, captions `[CC]` toggle, volume mute button with horizontal level slider, and fullscreen button (`⛶`).
  - Dynamic floating subtitles badge anchored at bottom-center of video containers displaying live transcript segments.
- **Sequence Preview Timeline Playback Unification**:
  - Sequence Preview video controls now drive playback across the entire multi-clip timeline sequence and scrub the global playhead.
  - Removed redundant play button from the timeline track header to eliminate duplicate chrome.
- **Backdrop Blur & Cursor Aura Overlays**:
  - Processing folder overlay suppresses cursor radial aura over the options card, displaying glow exclusively in the backdrop.
  - Upgraded Custom Collections "Add Media" (`LibraryPickerDialog`) into a frameless translucent overlay with desktop background blur, centered card container, outside-click dismissal, and outer-only cursor glow.
- **Sequence Media Declutter & Relink Migration**:
  - Replaced text toggle switch with dedicated list (`☰`) and grid (`⊞`) symbol buttons featuring interactive accent orange highlight.
  - Removed redundant outer card frames and excessive margins for a cleaner presentation.
  - Relocated "Relink offline media" action into the Sequence Media header, removing it from the Export Queue.
- **Story Timeline Toolbar Polish**:
  - Removed redundant track lock/hide actions from toolbar palette.
  - Reorganized remaining tools into a balanced 2-row tool board (`toolsBoard`).
  - Flanked timeline zoom slider with interactive `−` (zoom out) and `+` (zoom in) buttons.
- **Premiere FCP 7 XML Conformity**:
  - Audited and updated `timeline.final_cut_xml` generator with explicit `<rate>`, `<duration>`, source in/out frame bounds, and media `<file>` specifications.

---

## 1.23 — Polish & Finishing

- Beta feature toggle above GPU/VRAM/RAM meters; defaults off and persists across sessions.
- Beta-off hides Paper Edit and Visual Indexing throughout the app; library picker subtitle adjusted.
- Double-clicking the Tracer icon or wordmark opens Transcape.
- Transcape rebuilt with force-directed physics layout, data-weighted node sizes, cluster seeding, fluid motion, cursor repulsion, proximity labels, middle-mouse panning, wheel zoom, spatial reveal, Esc-to-exit, and frameless HUD chrome.
- Storyline Sequence Media uses a Select Collection dropdown and collection thumbnails.
- Storyline tools reorganized into two compact rows.
- Timeline Delete, ripple-delete, split, playback, clipboard, undo and redo shortcuts improved; Ctrl+Y redo added.
- Paper Edit restyled as a clean document-like sheet.
- Library video preview separated from transcript/frames/details with a resizable splitter.
- Processing overlay resized and made dismissible by clicking outside.
- Queue Add Media interaction made more noticeable.
- Subtle global cursor aura, stronger over the sidebar.
- Fixed transcape seed_layout infinite loop, O(N²) tick loop, and dead code.
- Cleaned unused imports in transcape.py and timeline_tools.py.
- Version, installer, and release documentation updated to 1.23.

---

## 1.22 — Feature Completion & Finishing

- Corrected the 1.21 Paper Edit regressions: manuscript state updates immediately again while linked-sequence synchronization is independently debounced.
- Paper Edit resolves and updates its exact linked Storyline sequence, keeps stable passage/clip identity across repeated synchronization, and exposes include/restore plus story order through the existing Passage Order panel.
- Storyline-to-Paper trims now resolve the correct manuscript by sequence identity instead of depending on whichever Paper document happens to be open.
- Replaced the `V A B C H Z` letter buttons with native symbol-led tools, consistent visual states, accessible labels, and guarded Premiere-style shortcuts.
- Track Select and Ripple edits now participate in undo, respect locked tracks, and preserve linked A/V trimming.
- Paper Edit protects manuscript width at the narrow supported layout; Storyline flattens duplicate one-file media rows in its compact media panel.
- Unified remaining Collection terminology and updated release packaging metadata to 1.22 / SCG.
- Added focused 1.22 regression coverage and a new wide/narrow rendered journey verifier.

---

## 1.21 — Finishing & Publishing Release

- **Shared Passage Model & Diff Synchronizer**: Paper Edit and Storyline become two views of the same sequence. Paper Edit edits the spoken-story spine; Storyline edits the full audiovisual assembly. Stable `passage_id` links manuscript passages to timeline clips without clobbering B-roll or extra audio tracks.
- **Bi-Directional Timing Sync**: Reordering or trimming in Paper Edit ripples spoken clips live; trims in Storyline reflect back as adjusted timestamps in Paper Edit marked as manual adjustments.
- **Timeline-Aware Manuscript UI**: Quiet gutter badges, live passage timing (`[start–end · dur · quality]`), source preview button, in/out trim dialog with reset-to-original, split-at-caret with proportional timestamp estimation, and sync status badge (`Synced to Storyline · X passages · MM:SS`).
- **Premiere-Style 6-Tool Storyline Dock**: Compact tool dock with Selection (`V`), Track Select Forward (`A`), Ripple Edit (`B`), Razor (`C`) with hover guide, Hand (`H`) viewport pan, and Zoom (`Z`).
- **Timeline Keyboard Shortcuts & Text-Focus Guard**: Premiere editing conventions (`Space`, `Left`/`Right` frame stepping, `Up`/`Down` edit jumps, `Ctrl+K` split at playhead, `Delete` / `Shift+Delete` ripple delete). Application-level focus guard prevents single-letter tool shortcuts from triggering when typing in text fields or search boxes.
- **Journey Polish & Diagnostics**: Unified vocabulary (Footage, Collection, Paper Edit, Storyline, Sequence, Export), single-action empty states, rotating diagnostic logging (`tracer.log`), and sanitized path redaction.

---

## 1.20 — Collection Unification & Continuous Manuscript

- Direction: Calm, neutral footage workspace with continuous manuscript and direct timeline manipulation.
- Collections unify legacy projects and lightweight collections while preserving IDs, media membership, timelines, and export queues.
- Continuous manuscript editor supports fluid typing, selection, deletion, undo, and source-aware internal copy/paste.
- Storyline has initial Select and Cut tools, exact playhead splits, and compact searchable media bin.
- Transcape visualization experience emerges by weight; pan, zoom, and focus connections.

---

## 1.19.2 — Midday Editorial Redesign

- **Midday-Inspired Dark Editorial Theme**: Unified palette using near-black `#0c0c0c` backgrounds, refined neutral grays (`#ededed` / `#878787` / `#5a5a5a`), crisp focus states, and warm amber search highlights (`#f59e0b`).
- **Sidebar & Navigation Overhaul**: Expanded navigation rail with dynamic Collections and Projects browser, prominent `+` creation button for both new collections and projects, right-click context menu (rename, delete, export files), and project-based Library filtering. Resource monitors (GPU / VRAM / RAM) and app version preserved.
- **Library Table View**: Replaced flat list with a rich 5-column table displaying video checkboxes, rounded video thumbnails, bold titles, duration, hit badges, and overflow menus (`···`).
- **Preview Action Bar**: Relocated "Open Results" and "Show in Explorer" above the preview video player, joined by a direct "Add to Project" dropdown (defaulting to latest project) and a quick `+` new project button.
- **Visual Index Inspector Tab**: Dedicated inspector tab displaying all detected objects and scene moments with timestamps, layer badges (`[F]` foreground, `[M]` midground, `[B]` background), confidence percentages, live search filtering, and click-to-seek playback.
- **Project Selection when Processing Folders**: Integrated project assignment as the top option in `OptionsDialog`, defaulting to the latest project with an instant `+` creation button, automatically routing finished video records into the target project.
- **Paper Edit "Word Document / Notepad" Feel**: Eliminated rigid card boxes for a fluid, continuous manuscript document layout with clean margin timecodes, inline uppercase speaker badges, and fixed high-contrast "Export script" icon.
- **Progress Bar & Control Contrast**: Modern `#2563eb` accent chunk with `#ededed` text on `QProgressBar` ensuring 100% readability across all percentages; replaced text "Pause" button with intuitive pause icon.

---

## 1.18

- Queue delete retains its selected target through refresh and removes queue entries without deleting source media.
- Clicking visual search results loads the source and seeks to the matched timestamp. Pending seeks survive asynchronous media loading.
- Colored, larger origin icons appear beside match counts. Visual-only results show visual counts without direct/indirect transcript counts.
- AI sampling uses Capture every or Scene changes. Boundary sampling remains enabled. Redo existing results updates old indexes.
- Processing and preview sliders jump to the clicked location and support continuous dragging.
- Empty Storyline sequences expose editing controls. Portrait/Landscape layout buttons sit beside Storyline; preview minimum sizes are reduced and Export Queue moves into the top-right toolbar popup.

---

## 1.17

- Fixed interaction defect preventing fixed-interval vs scene-change screenshot capture selection.
- Added 1–30 second AI sample-distance control and start/end boundary sampling.
- Improved NanoDet-backed object search with deterministic aliases, plural normalization, category groups, confidence-aware ranking, adjacent-frame voting, and grouped moments.
- Added compact search-origin indicators for transcript, visual, and filename matches.
- Connected Storyline scrubbing to the sequence preview, anchored zoom to the playhead, added edit/marker/playhead snapping and playback auto-scroll, and persisted playhead, zoom, and horizontal scroll per sequence.
- Added explicit gap and offline preview states and removed the unwanted zoom-slider focus rectangle.
- Simplified the left-rail footer to GPU, VRAM, RAM, and version information.
- Added editing-first About copy and AI preview-cache cleanup action.
- Reduced visual-index storage by retaining thumbnails only for detections, using smaller optimized previews, and limiting the per-video detail cache.

---

## 1.16 — Modular Desk

- Shared native dock system: page-specific layouts, rearrangeable panels, resizable dividers, focus/restore, panel menus, named save/restore, reset, and full-screen controls.
- 76 px primary rail with 18 px navigation icons; Queue, Library, Paper Edit, Storyline, Settings.
- Graphite surfaces, orange selected states, compact toolbar icons, readable focused controls.
- Paper Edit Write/Find modes plus Build shortcut into Storyline; persistent cross-video search with excerpts, word highlights and direct/indirect counts.
- Independent Source Preview and Visual References; working scrub/playback controls, clickable frames, and explicit offline status.
- Vertical Passage Order panel with drag and Move up/down; no permanent editing timeline on Paper Edit.
- Library transcript/search/preview/reference docks with three layout presets.
- Storyline media/preview/timeline/export docks, compact edit icons, ruler dragging, zoom synchronization, and cached real Library thumbnails.
- Shutdown disposes players through Qt's deferred object cleanup instead of synchronous closeEvent stopping.

---

## 1.15 and earlier

See version snapshots under `versions/` and release notes under `docs/product/` for historical details.
