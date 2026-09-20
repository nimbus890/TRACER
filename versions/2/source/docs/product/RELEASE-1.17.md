# Tracer 1.17 release record

## Delivered

- Fixed an interaction defect that prevented choosing between fixed-interval and scene-change screenshot capture.
- Added a 1–30 second AI sample-distance control and start/end boundary sampling.
- Improved NanoDet-backed object search with deterministic aliases, plural normalization, category groups, confidence-aware ranking, adjacent-frame voting, and grouped moments.
- Added compact search-origin indicators for transcript, visual, and filename matches.
- Connected Storyline scrubbing to the sequence preview, anchored zoom to the playhead, added edit/marker/playhead snapping and playback auto-scroll, and persisted playhead, zoom, and horizontal scroll per sequence.
- Added explicit gap and offline preview states and removed the unwanted zoom-slider focus rectangle.
- Simplified the left-rail footer to GPU, VRAM, RAM, and version information.
- Added the approved editing-first About copy and an AI preview-cache cleanup action.
- Reduced visual-index storage by retaining thumbnails only for detections, using smaller optimized previews, and limiting the per-video detail cache.

## Verification

- 40 automated tests pass.
- Processing-mode, sampling-range, boundary-sampling, object-query, moment-grouping, and timeline-state checks are included.
- The modular workspace acceptance run passes with the native Windows Qt backend and verifies preview seeking, playhead-anchored zoom, and saved sequence view state.
- Rendered Library and Storyline states were visually inspected at desktop resolution.

## Intentional limits

- NanoDet and the existing semantic/transcript architecture were not replaced.
- Small-object crop passes and class-specific thresholds are deferred.
- Visual search remains an 80-class COCO object index with deterministic query assistance, not general semantic scene understanding.
- Premiere delivery remains importable Final Cut Pro 7 XML rather than a native `.prproj` file.
