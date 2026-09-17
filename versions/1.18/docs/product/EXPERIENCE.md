# Tracer experience

## 1.17 interaction refinement

Processing makes its capture mode explicit: Fixed interval and Scene changes are mutually exclusive, and interval controls only appear available when they apply. AI sample distance runs from 1 to 30 seconds. A quiet inline note explains that changed settings apply to future jobs and that Redo existing results refreshes indexed footage.

Search results identify whether a hit came from transcript text, visual objects, or the filename using small unboxed symbols. Consecutive visual detections become one moment rather than repeated frames; the strongest frame represents the moment.

In Storyline, the playhead is the anchor for preview and zoom. Scrubbing updates the preview, zoom preserves the playhead's position in the viewport, playback auto-scrolls, and snapping targets edits, markers, and the playhead. Each sequence remembers playhead, zoom, and horizontal scroll. Gaps and offline clips display explicit preview states.

## 1.16 Modular Desk

The user-approved 1.16 corrections supersede earlier screen placement: launch on Queue and keep the left rail primary, in Queue / Library / Paper Edit / Storyline / Settings order. Write and Find are Paper Edit workspace arrangements. Build opens the dedicated Storyline page. Paper Edit has no permanent bottom timeline; Passage order is a contextual vertical dock.

Paper Edit Find keeps results beside the script while changing videos. Search authored wording when it exists; retain edits when switching sources. No-match results explain recovery without discarding the current document. Offline media keeps the transcript usable and reports preview unavailability.

Paper Edit, Library and Storyline use native dockable panels. Every panel provides movement by header dragging or menu commands, focus/restore, and collapse. Layout provides presets, panel recovery, named save/restore, and reset. Each page owns independent layout memory. Escape restores a focused panel; F11 toggles the window full screen.

Source preview and visual references are independent; the Storyline timeline can be resized and rearranged within its own page. Its export panel is normally collapsed. Existing source-selection, sequence export, and local processing behavior remains protected.

## Primary journey
Queue imports and processes footage. Library lets users search and inspect it. Paper Edit creates an independent writer document from a result, with editable passages, speaker labels, notes, includes, and order. Export delivers the currently selected paper sequence. Storyline provides the simple visual assembly route.

## Upgrade decisions
Selections in the Library chooser belong to the entire chooser, not the visible search result set. Searching another term must retain previous checks and the Add count. A no-match search clears stale preview content and keeps the selection count available.

An existing writer document belongs to the user. Re-adding its source opens that document without replacing it with a new machine transcript.

Passage text controls fit their contents within a practical height cap; the page supplies the main scrolling. Detailed repeated terms go into the analysis tooltip so search retains usable width.

Export captures the document at the moment the user starts, disables repeat export until completion, and restores actions on failure. Invalid or empty selections produce a clear error before any output folder is made.

## Preserved interactions and limits
Keep manual include checkboxes, script search, pen/marker, timecode playback, and passage dragging. Multiple Library selections create separate source documents; cross-source paper stories are not yet implemented. Source timing remains segment-level when text changes.
