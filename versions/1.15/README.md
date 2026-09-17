# Tracer 1.15

Tracer is a local Windows workspace for turning video folders into searchable transcripts, screenshots, paper edits, and simple Premiere-ready story sequences.

## Open the app

Double-click **Launch Tracer.vbs** to open the working build. Tracer keeps source media in place and stores its local library, models, and editing state under **data**.

The editable 1.15 source is preserved under **versions/1.15**. Earlier snapshots remain under **versions**. No 1.15 executable or installer is created unless an exportable build is explicitly requested.

## Paper Edit

Paper Edit is the first page and is designed for writers and storytellers. It uses Tracer's normal dark editing palette while retaining its manuscript typography and transcript-first layout.

1. Choose **Library**, search processed footage, tick any number of videos, and add them together.
2. Edit transcript text and speaker names directly. The machine transcript remains available as original text in the saved Paper Edit data.
3. Untick a passage to exclude it, mark a key line, or write a red margin note.
4. Use the pen or marker icons to draw freehand annotations. Undo removes the latest stroke; Clear removes all strokes after confirmation.
5. Drag passage cards in **Paper Sequence** to change story order. Clicking a timecode plays the original source from that line.
6. The header reports honest local analysis: word count, selected-passage count, and frequently repeated terms. It does not pretend to infer themes or story meaning.
7. **Export script** creates a new collision-safe folder containing the edited script, Paper Edit JSON, a manifest, individually trimmed MP4 passages, and a Premiere-importable Final Cut Pro 7 XML timeline in paper order. Original media is never moved or modified.

## Storyline

Storyline is a deliberately simple sequence workspace rather than a project-management dashboard.

- **Open Video Library** opens a searchable overlay with transcript-hit counts, highlighted transcript context, visual frames, and checkbox-based multi-video selection.
- Added footage can be appended, dragged, repositioned, split, cut, copied, pasted, duplicated, deleted, undone, and redone.
- Dropping footage on an occupied video layer automatically creates another video layer above it. Linked sound uses the first open audio layer or creates a new one, so the stack has no fixed track limit.
- The sequence has play/pause, a playhead, zoom, fit, markers, and track visibility, mute, solo, and lock controls.
- Multiple sequence tabs remain available. Delivery stays collapsed until requested; sequences can be dragged or sent to its compact export queue.
- Delivery can export Premiere XML, relink offline media, or collect only used source files into a portable folder with a rewritten XML and manifest.

## Queue and native Windows imports

**Add media** now opens the native Windows multi-file picker. This restores the normal Explorer appearance, navigation arrows, scaling, and keyboard behavior. To add folders, or folders and loose videos together, drag them directly from Windows Explorer onto Tracer.

Folders process from top to bottom. Expand a folder to include or exclude individual videos, reorder folders with the arrow buttons, and use **Rescan** to discover new files. The sharp opaque trash icon removes the selected queue entry without deleting anything from disk.

The processing dialog can create transcripts, screenshots, and a local visual index. Screenshot spacing supports exact 0.1–30 second values or scene-change detection. Advanced controls expose device, image size, and installed Whisper models. Processing progress is weighted across the complete selected batch.

## Video Library

The Library searches source names, transcript text, and locally indexed visual keywords. Its result rail stays open while moving between videos and collapses when clicking outside it. The transcript, source preview, and screenshots reflow around the rail instead of being covered.

Each result distinguishes direct token-prefix hits from embedded hits. Transcript matches are highlighted, compact arrow icons move through matches and screenshot pages, and **Show in Explorer** opens the source file highlighted in Windows Explorer.

## Display and local status

Tracer enables per-monitor Windows DPI awareness, pass-through scale-factor rounding, and high-resolution drawn icons to avoid the gray, soft appearance caused by bitmap scaling. The narrow navigation uses icons plus labels.

Tiny GPU, VRAM, and RAM meters show **Tracer usage / total system usage** as percentages. They are sampled locally. Unsupported readings show an em dash.

## Processing and privacy

Processing is local after models are installed. Folders are processed in order, one video at a time; the enabled transcript, screenshot, and visual-index stages run concurrently for that video. Pause and cancel are cooperative and may wait for the current decoded frame or transcript operation.

New outputs normally live inside **Tracer Results** beside the source. Each run uses a collision-safe directory and can include TXT, SRT, VTT, JSON, screenshots, a visual index, and processing details. Original videos are never modified. Matching completed runs can be reused unless **Redo existing results** is enabled.

Tiny Whisper and the lightweight NanoDet object detector are the default local models. Settings can install larger Whisper models. Downloading a model contacts Hugging Face; footage is not uploaded.

## Known limits

- Transcript text and timing are model predictions. Speaker identification is manual in Paper Edit.
- Repeated-term analysis is deterministic word counting, not semantic or generative story analysis.
- Visual search recognises a limited object vocabulary and uses approximate screen-space depth.
- Video playback depends on Qt/FFmpeg codec support.
- Premiere export uses Final Cut Pro 7 XML for import compatibility; it is not a native .prproj file.
- The native Windows picker selects multiple files. Mixed folder-and-file selection is provided through Explorer drag-and-drop because the standard Windows picker does not combine those modes.

## Development

Use Python 3.12 on Windows x64, install **requirements.txt** in a virtual environment, and run **python app.py**.

- Automated checks: python -m unittest discover -s tests -v
- Interface verification: python verify.py ui
- GPU processing verification: python verify.py gpu
- Build: python build.py, then compile **Tracer.iss** with Inno Setup 6.7 or newer

Generated verification media is synthetic and does not use user footage.
