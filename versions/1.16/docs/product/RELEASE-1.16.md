# Tracer 1.16 — Modular Desk

## Accepted direction

The user chose concept 02 and approved implementation on the existing foundation. Queue starts first; the left rail remains primary navigation with smaller icons. Paper Edit has no full-width bottom timeline. Storyline remains a dedicated page. The reference includes actual interactions, not merely colors: workspace modes, layouts, resizing, panel movement, focus, zoom, and compact export.

## Delivered

- Shared native dock system in workspace.py: page-specific layouts, rearrangeable panels, resizable dividers, focus/restore, panel menus, named save/restore, reset, and full-screen controls.
- 76 px primary rail with 18 px navigation icons; Queue, Library, Paper Edit, Storyline, Settings.
- Graphite surfaces, orange selected states, compact toolbar icons, readable focused controls.
- Paper Edit Write/Find modes plus Build shortcut into Storyline; persistent cross-video search with excerpts, thumbnail availability, word highlights and direct/indirect counts.
- Independent Source Preview and Visual References; working scrub/playback controls, clickable frames, and an explicit offline status.
- Vertical Passage Order panel with drag and Move up/down; no permanent editing timeline on Paper Edit.
- Library transcript/search/preview/reference docks, three layout presets and continued outside-click result collapse.
- Storyline media/preview/timeline/export docks, compact edit icons, ruler dragging, zoom synchronization, and cached real Library thumbnails.
- Shutdown disposes players through Qt's deferred object cleanup instead of synchronously stopping hidden decoder pipelines inside closeEvent.

## Source reference

- Repository: https://github.com/penpot/penpot
- Workspace tree inspected: https://github.com/penpot/penpot/tree/develop/frontend/src/app/main/ui/workspace
- Toolbar source inspected: https://github.com/penpot/penpot/blob/develop/frontend/src/app/main/ui/workspace/top_toolbar.cljs
- Borrowed principles: context-specific toolbar visibility, grouped tools, explicit selection states, labelled icon controls, and collapsible workspace areas.
- Native Qt docking, presets, and layout serialization are Tracer implementations. No Penpot source was vendored.

## Verification

- 37 regression tests, including four new workspace/search recovery tests.
- Full synthetic UI flow through Paper Edit, Queue, processing options, stacked Storyline, export queue, Library, Settings and shutdown.
- Dedicated modular acceptance at 1440×900 and 1100×720; Queue startup, Find, word highlights, no-match/offline recovery, focus restore, passage order, stack creation, zoom synchronization, and export dock.
- The modular acceptance also runs with native Windows rendering. Source preview reports BufferedMedia, a 15.3-second fixture duration, and no player error.
- Screenshots use synthetic footage and illustrative transcript text; they contain no user footage.

## Current limits

Paper documents remain source-specific; Build opens Storyline and does not silently convert a paper script into a new timeline. Sequence playback retains the existing single-source preview limitations, not full multitrack audio mixing. Exports remain Premiere-importable XML, not native .prproj files. Panel state is stored on navigation/close or explicit Save layout. No standalone installer was built.
