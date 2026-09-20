# Tracer 1.20

Direction: a calm, neutral footage workspace with a continuous manuscript and
direct timeline manipulation. Retains the approved Tracer artwork.

## Delivered journeys

- Library searches all indexed footage and collection names. Export project is
  absent here. The collection destination and create button live below the file
  list. Selection exposes select-all, deselect, and original-file export.
- Collections unify old projects and lightweight collections, preserving IDs,
  media membership, timelines and export queues. A separate collection page
  keeps its sidebar selection without activating Library. Export project copies
  original media. Add media selects indexed footage. Paper Edit and Storyline
  are direct collection actions. Raw footage can still be imported through Queue.
- Paper Edit defaults to Search beside script. Write/Find/Build mode buttons are
  removed; alternate arrangements remain under Layout. One continuous text
  editor supports selection, typing, deletion, undo, and source-aware internal
  copy/paste. Source timing is passage-level, not inferred word alignment.
- Included manuscript passages update one linked sequence. If a linked sequence
  has manual timeline edits, a separate Storyline cut is preserved before a new
  paper update replaces the linked assembly. This is not bidirectional transcript
  rewriting from timeline edits.
- Storyline has Select and Cut tools, exact playhead splits with independent
  right-hand A/V links, a compact searchable media bin, and a sequence-position
  preview slider. No top-right + Sequence button. Existing sequence tabs remain.
- Paper Edit and Storyline offer Export as Premiere (FCP7 XML for import) and
  Export as Project (original used media, sequence JSON, XML and manifest; Paper
  Edit also includes its script/document). This does not generate .prproj files.
- Double-clicking the top-left logo opens Transcape. It uses existing transcript
  terms, visual labels, authored speakers, files and collections. Nodes emerge
  by weight; pan, zoom, focus connections, and double-click source moments.
  Escape returns to Tracer. It computes no new AI inference or semantic claims.

## Data and recovery

The first 1.20 launch backs up pre-migration state to
`data/library-before-1.20.json` when a saved library exists. The legacy projects
key remains a compatibility adapter to the same collection objects. Export
deduplicates source paths, preserves filename collisions, and reports missing
and failed copies. Original source media is unchanged.

## Verification and limits

52 automated tests pass. Isolated UI checks cover Library selection, separate
Collection navigation, manuscript editing and undo, shared sequence identity,
preview slider synchronization, Cut and undo. Rendered at 1440×900 and 1100×720,
including offline and empty states. Screenshots are in verification/1.20.

Native GPU inference and installed Premiere import were not rerun. Transcape
currently displays a bounded overview of up to 90 files with prominent terms;
links describe source evidence, not inferred semantic relationships. The supplied
version is a runnable source snapshot using the existing Python environment,
not a newly built installer. The requested upgrade/ship passes are subsequent work.
