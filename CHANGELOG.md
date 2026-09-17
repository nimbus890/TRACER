# Tracer Changelog

All notable changes to Tracer are documented here. Versions follow the existing snapshot numbering.

---

## 1.19.2 — In Progress

UI iteration pass. Details to be added as changes land.

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
