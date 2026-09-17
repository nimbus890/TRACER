# Tracer experience

## Primary journey
Queue imports and processes footage. Library lets users search and inspect it. Paper Edit creates an independent writer document from a result, with editable passages, speaker labels, notes, includes, and order. Export delivers the currently selected paper sequence. Storyline provides the simple visual assembly route.

## Upgrade decisions
Selections in the Library chooser belong to the entire chooser, not the visible search result set. Searching another term must retain previous checks and the Add count. A no-match search clears stale preview content and keeps the selection count available.

An existing writer document belongs to the user. Re-adding its source opens that document without replacing it with a new machine transcript.

Passage text controls fit their contents within a practical height cap; the page supplies the main scrolling. Detailed repeated terms go into the analysis tooltip so search retains usable width.

Export captures the document at the moment the user starts, disables repeat export until completion, and restores actions on failure. Invalid or empty selections produce a clear error before any output folder is made.

## Preserved interactions and limits
Keep manual include checkboxes, script search, pen/marker, timecode playback, and passage dragging. Multiple Library selections create separate source documents; cross-source paper stories are not yet implemented. Source timing remains segment-level when text changes.
