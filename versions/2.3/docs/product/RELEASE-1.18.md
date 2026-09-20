# Tracer 1.18

- Queue delete retains its selected target through refresh and removes queue entries without deleting source media.
- Clicking visual search results loads the source and seeks to the matched timestamp. Pending seeks survive asynchronous media loading. Keyboard result navigation also updates the preview.
- Colored, larger origin icons appear beside match counts. Visual-only results show visual counts without direct/indirect transcript counts.
- AI sampling uses Capture every or Scene changes. Opening/closing boundary sampling remains enabled. Redo existing results updates old indexes.
- Processing and preview sliders jump to the clicked location and support continuous dragging.
- Empty Storyline sequences expose editing controls. Portrait/Landscape layout symbols sit beside Storyline; preview minimum sizes are reduced and Export Queue moves into the top-right toolbar popup.

Verification includes the automated suite, rendered UI and modular acceptance checks, and a dedicated native Windows regression covering queue removal, source preservation, slider clicking, an 8-second visual-result seek, subsequent playback, empty-sequence creation, and preview collapse/recovery. Synthetic footage is used; source files and old version snapshots remain intact.

Scope: object detection remains NanoDet. Orientation buttons arrange the workspace; sequence output dimensions remain controlled by Sequence Settings. This is a source release using the existing runtime, not a new installer.
