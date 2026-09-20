# Tracer 1.22 — Feature Completion & Finishing

Direction: finish the editing work introduced in 1.21, then improve the existing product rather than expanding it.

## Editing completion

- Paper Edit updates its document state immediately and debounces only the heavier Storyline synchronization.
- Passage order and included/excluded state control the linked speech sequence. Excluded passages can be restored from the existing Passage Order panel.
- Repeated synchronization retains passage and clip identity and preserves Storyline-only tracks.
- Storyline trims resolve the manuscript through the sequence's `paper_document_id`, even when another document is open.
- Storyline uses symbol-led Selection, Track Select, Ripple, Razor, Hand, and Zoom controls. Tooltips retain their familiar shortcuts.
- Timeline keyboard commands are routed through one text-focus guard so editing shortcuts cannot fire while typing.
- Track Select and Ripple changes enter the existing undo flow; Ripple respects locked linked tracks and trims linked A/V together.

## Finishing work

- Paper Edit automatically collapses secondary preview panels at the minimum supported width so the manuscript remains usable.
- The active passage summary is quieter and easier to scan.
- Storyline flattens duplicate parent/child rows when a source contains only one media file.
- Collection vocabulary is consistent in current user-facing actions and feedback.
- Windows installer metadata now reports Tracer 1.22.0 and SCG.

## Verification

- 66 automated tests pass; one existing environment-dependent test is skipped.
- `verify_122.py` exercises the primary UI journey and renders Queue, Library, Collection, Paper Edit, Storyline, Transcape, narrow layouts, offline media, and empty Library states.
- Rendered screenshots are stored under `verification/1.22/`.
- The final standalone Windows build launches successfully with isolated data and embeds the correct `1.22` version metadata.
- The standalone executable is at `dist/Tracer/Tracer.exe`; its SHA-256 is `45BED9AF4E93A4AA5E4E2029B6801CC671BD86DD937C3CA76CEC3A51E5B03A8D`.

## Boundaries

- No new workspace, inference model, visualization mode, framework, or advanced editing family was added.
- Transcript timing remains passage-level unless the user explicitly adjusts or splits a passage.
- Native GPU inference, installed Premiere import, and code-signed installer behavior require machine-level release validation.
- Inno Setup is not installed on the current workstation. The installer definition is ready, but the setup executable remains a release-machine task.
