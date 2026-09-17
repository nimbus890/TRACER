# Tracer product notes

## Version 2 direction: Story Editor

The Story Editor should be a separate left-navigation workspace built on the media already indexed by a Tracer project. It should remain useful without generative AI.

### Core interaction

- Open a project and create one or more named story drafts.
- Search exact transcript text, filenames, notes, and existing visual keywords.
- Add either a spoken transcript range or a visual moment to a story sequence.
- Keep transcript text, source timecode, thumbnail, in/out points, notes, and source-file reference linked as one non-destructive story item.
- Reorder story items, trim their in/out points, add section cards, and mark selects, alternatives, favourites, or rejected material.
- Selecting a transcript line should reveal the corresponding image and video moment; selecting a visual result should reveal nearby dialogue and transcript context.
- Offer visual alternatives for a spoken section so an editor can pair dialogue with indexed B-roll without leaving the Story Editor.

### Recommended layout

- Left: project bins, saved searches, sequences, and story-draft versions.
- Centre: the paper-edit/story sequence, readable primarily as transcript blocks with timecodes.
- Right: source preview and a contextual visual-results strip tied to the selected story item.
- Bottom or collapsible inspector: notes, tags, in/out controls, source path, and export status.

### Export package

The default export should reference original media rather than copy or move it. Moving source media is too risky, and copying every source wastes space.

Each export can create one clearly named folder containing:

- a readable story transcript;
- a structured Tracer story/project file for reopening the edit;
- a Premiere-importable timeline exchange file with source paths, timecodes, cuts, and markers;
- optional subtitle and marker files;
- an export report listing missing or offline media.

An explicit **Collect used media** option can later copy only media used by the story into the export folder. It should never move originals.

## Project-management improvements

- Treat projects as non-destructive references to source folders and files.
- Add bins, colour labels, notes, favourites, rejects, review status, and custom tags.
- Allow multiple named story drafts and snapshots inside one project.
- Save project-specific searches, processing defaults, and export history.
- Show missing/offline media and offer relinking without losing transcript or visual-index work.
- Track processing coverage at project level: transcript ready, frames ready, visual index ready, failed, or stale.
- Provide duplicate detection and one canonical media record even when a source appears in several folders or batches.

## Search strategy

Fully semantic transcript search is not required for the first Story Editor. Fast exact-word and phrase search, transcript timestamps, project metadata, notes, and current visual keywords are enough to build a strong editor workflow.

Semantic transcript search can be added later as an optional local index when users need intent-based queries such as “the part where she explains the setback” even though those exact words were never spoken. It should augment the dependable exact search rather than replace it.

## Later offline-AI beta

- Build the assistant on saved transcript segments, visual-index records, notes, and story selections instead of rescanning raw footage for every question.
- Add local embeddings for meaning-based transcript and visual retrieval.
- Expand visual analysis beyond objects to shot type, movement, lighting, palette, location cues, composition, and production-design language.
- Let the assistant suggest quotes, themes, possible story structures, B-roll pairings, and alternate selects, while requiring the editor to approve changes.
- Keep the assistant optional, offline, and visibly separate from deterministic search and manual editing.

## Unpolished comparison

The Unpolished project was not found in the currently accessible `C:\projects` folders. Once its location is provided, compare its project model, visual-language analysis, review workflow, and reusable interface patterns before implementing Tracer 2.
