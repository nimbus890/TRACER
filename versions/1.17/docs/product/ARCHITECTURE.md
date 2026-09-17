# Tracer architecture decisions

## Drivers
Protect authored work, preserve offline behavior, avoid stale asynchronous state, and keep the current desktop stack maintainable.

## Boundaries
Qt owns widgets and interactions. Window owns the saved library and worker lifetimes. paper_edit owns writer-document creation, analysis, sequence construction and package export. timeline owns clip structures and XML. core owns media processing and atomic library persistence.

## Decisions for this upgrade
- Existing paper documents are immutable with respect to machine-transcript refresh: user editing is authoritative. Return an existing document for the same source/result; no automatic destructive remapping.
- Library selection is an ID set independent of filtered widgets. The UI reconciles visible check changes into that set.
- Export receives a deep copy captured on the UI thread. A busy flag prevents duplicate launch. Failure resets the action.
- Validate selected ranges and source availability before writing. Mark exports as building, complete or failed through the manifest so incomplete packages do not imply success.
- Keep Qt/PyAV and existing state schema; no dependency update or data migration.

## Verification
Regress search persistence, machine-refresh preservation, invalid export preflight, failed package status, real trim duration, and compact row resize. Inspect desktop and narrow renders.

## Remaining risks
The single app module still couples multiple workspaces. PyAV trimming uses frame boundaries and re-encoding; it is not sample-accurate word editing. Storyline playback currently previews a picture source rather than mixing every audio track. Reassess those boundaries before promising a full editing engine.
