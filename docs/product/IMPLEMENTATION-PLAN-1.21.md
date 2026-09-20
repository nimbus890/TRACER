# Tracer 1.21 — Finishing & Publishing Implementation Plan

**Status:** Proposed; implementation has not started; approval required.  
**Scope:** A focused finishing release based on the current 1.20 build. Fix the editing model, improve the primary journey, remove friction, and prepare Tracer for publishing. Large product changes are recorded separately and are not part of 1.21.

## Target outcome

Tracer should feel like one coherent editing product:

> Add footage → find useful material → organize it in a Collection → shape the spoken story in Paper Edit → finish the audiovisual sequence in Storyline → export.

The central change is that Paper Edit and Storyline become two views of the same sequence:

- **Paper Edit owns the spoken-story spine:** transcript text, passage order, inclusion, and dialogue in/out points.
- **Storyline owns the complete audiovisual assembly:** the same spoken-story clips plus B-roll, additional audio, track controls, and detailed timeline work.
- Both use stable passage and clip identities, so a change in one view updates the shared sequence without silently destroying work in the other.

## Current 1.20 baseline

Already present and worth protecting:

- Library and Collections have distinct purposes and screens.
- “Projects” are presented as Collections while old saved data remains compatible.
- Paper Edit is a continuous, document-like manuscript.
- Paper Edit can generate a linked Storyline sequence.
- Manual Storyline work is protected by preserving a separate cut when the Paper Edit sequence is rebuilt.
- Storyline has initial Select/Cut behavior, a synchronized playhead, and export choices.
- Transcape exists as the hidden visualization experience.
- Automated checks and rendered screenshots provide a usable 1.20 baseline.

The main gap is not the absence of a connection. It is that the connection is mostly invisible, rebuild-oriented, and difficult for the user to control.

## Principles for this pass

1. **Document first.** Paper Edit must still feel like writing, not a timeline covered in controls.
2. **One sequence, two editing views.** Shared edits have shared results; view-specific work is preserved.
3. **Visible cause and effect.** Every edit communicates what changed, where, and whether it is saved and synchronized.
4. **Familiar where useful.** Storyline borrows proven editing conventions without pretending to be all of Premiere.
5. **Progressive disclosure.** Advanced controls appear when a passage, clip, or tool is active.
6. **Local and recoverable.** Background work, failures, autosave, migration, and export are clear and safe.

---

## P0 — Make Paper Edit a real timeline editor

### Shared passage model

Extend the existing source-segment identity rather than creating a second timeline system. Each spoken passage needs:

- a stable `passage_id` used in both views;
- source asset and transcript segment IDs;
- source in/out times;
- sequence order and included/excluded state;
- displayed manuscript text;
- timing quality: source, estimated, or manually adjusted;
- revision metadata for synchronization and undo.

The linked sequence references `passage_id` on A-roll/dialogue clips. B-roll, music, and other Storyline-only layers remain normal timeline clips.

### Ownership and edit rules

| User action | Paper Edit result | Storyline result |
|---|---|---|
| Reorder a passage | Paragraph moves | Spoken clip ripples to the new order |
| Remove passage from cut | Text may remain visible but becomes excluded | Spoken clip is removed and the gap closes |
| Restore a passage | Passage becomes included | Clip returns at its document position |
| Change passage in/out | Time badge and duration update | Same clip is trimmed and downstream clips ripple |
| Trim linked spoken clip in Storyline | Passage shows adjusted timing | Clip uses the new trim |
| Add B-roll/music/extra tracks | No prose is invented | Storyline-only work remains intact during Paper edits |
| Edit wording | Manuscript text changes | Timing stays unchanged unless split, joined, or trimmed |

This is intentionally not unrestricted two-way document merging. Paper Edit edits the narrative spine; Storyline finishes the cut around it.

### Timeline-aware document UI

Keep the page visually clean. Reveal a quiet passage control only on hover, keyboard focus, or selection:

- narrow left-gutter marker;
- start–end timecode and duration;
- included/excluded state;
- source preview button;
- drag handle for passage reorder;
- compact actions: **Trim**, **Remove from cut**, and **Restore**.

The resting page remains document-like. Add one subtle status line:

> Synced to Storyline · 18 passages · 02:14

Support **Saved**, **Syncing**, **Synced**, and **Needs review** states. Failed synchronization must never look saved.

### Simple timing behavior

- Transcript timestamps remain the default truth.
- Splitting at the caret uses word-level timestamps if available. Otherwise, estimate proportionally and visibly label the result **Estimated**.
- Apply a configurable dialogue handle to new passages—default **0.2 seconds before and after**, clamped to media and neighboring boundaries.
- The Trim action opens a compact in/out control with preview, reset-to-transcript, and keyboard nudging.
- Never fabricate media beyond source bounds or silently overlap adjacent speech.

### Safer synchronization

Replace full rebuilds during typing with one synchronization transaction:

1. Debounce document synchronization by about 350 ms.
2. Diff by stable `passage_id`.
3. Update only inserted, removed, reordered, or retimed spoken clips.
4. Preserve Storyline-only tracks and clip metadata.
5. Save the document and sequence together as one recoverable revision.
6. If a conflict cannot be resolved safely, preserve both versions and show a specific review message.

### Paper Edit cleanup

- Keep the current document + search/source layout.
- Remove layout choices that do not provide a materially different workflow.
- Allow transcript results to be inserted by drag, double-click, or **Add to Paper Edit**.
- After insertion, focus and reveal the new passage.
- Add standard undo/redo across prose and sequence-affecting passage operations.
- Use an empty state that teaches the actual journey, not the interface construction.

### Acceptance checks

- Reordering passages changes the Storyline order without losing B-roll.
- Deleting ordinary words does not accidentally delete a clip.
- Removing a passage from the cut removes the linked clip and can be undone.
- Splitting a passage creates valid, reviewable linked timing.
- Storyline trims appear as adjusted timing in Paper Edit.
- Failed save/sync is visible and recoverable.
- Reopening preserves text, passage identity, trims, order, and Storyline-only tracks.

---

## P0 — Redesign Storyline’s timeline tools

### Compact visual tool dock

Place one consistent tool group immediately above or to the left of the timeline. Use 32–36 px icon buttons, one selected tool at a time, a strong active state, and tooltips containing shortcuts.

| Tool | Shortcut | 1.21 behavior |
|---|---:|---|
| Selection | `V` | Select/move clips; default safe tool |
| Track Select Forward | `A` | Select clips to the right; `Shift` applies across tracks |
| Ripple Edit | `B` | Trim an edge while downstream clips move live |
| Razor | `C` | Split at pointer; `Shift` splits enabled tracks |
| Hand | `H` | Pan the timeline viewport |
| Zoom | `Z` | Click/drag to zoom; modifier reverses direction |

Editing and playback commands:

| Command | Shortcut |
|---|---:|
| Play/pause | `Space` |
| Previous/next frame | `Left` / `Right` |
| Previous/next edit | `Up` / `Down` |
| Add edit at playhead | `Ctrl+K` |
| Undo/redo | `Ctrl+Z` / `Ctrl+Shift+Z` |
| Delete selection | `Delete` |
| Ripple delete | `Shift+Delete` |
| Zoom in/out | `=` / `-` |

These follow familiar Premiere conventions. The tool icon, pointer, tooltip, and one-line status message must change together. Selection returns as the safe default.

Do **not** add Slip, Slide, Rolling Edit, Rate Stretch, Pen, or keyframe editing in this minor pass. They require deeper media and trim behavior and would be misleading if partly implemented.

### Put controls where their object lives

- Track add, visibility, mute, solo, and lock controls belong in track headers.
- Undo, redo, and snapping belong in the timeline bar.
- Clip actions appear in a selected-clip strip or context menu.
- Import/add footage belongs in the sequence media panel.
- Export remains at sequence level.

### Compact sequence media panel

- Dense thumbnail row with name, type, and duration; quiet secondary metadata only when useful.
- Search and one compact add/import action at the top.
- Drag affordance and double-click insert.
- Hide instructional copy after the first successful insertion.
- Clear loading, empty, no-results, offline, and error states.
- Resizable divider with a protected minimum timeline width.

### Timeline feedback

- Visually distinguish selected, linked, offline, and estimated clips.
- Give snapping a visible state and momentary guide.
- Preview the exact Razor position before the cut.
- Ripple trim previews downstream movement and sequence duration.
- Keep playhead, preview, and timecode synchronized during pointer drag and keyboard navigation.
- Prefer immediate undo to repetitive confirmation dialogs.

### Acceptance checks

- Every visible tool performs its named operation and has a working shortcut.
- Text-field focus prevents timeline letter shortcuts from firing.
- Pointer, active icon, tooltip, and status text agree.
- Select, Razor, Ripple, playhead navigation, undo, and redo work at multiple zoom levels.
- Linked clip identity survives edits and reload.
- B-roll/audio tracks survive Paper Edit changes.
- The media panel works at 1100×720 and feels comfortable at 1440×900.

---

## P1 — Primary journey and interaction polish

### Navigation and narrative

- Use one vocabulary: **Footage, Collection, Paper Edit, Storyline, Sequence, Export**.
- Remove user-facing “Project” language except the explicit output format **Export as Project**.
- Keep Settings visually separate from the creative journey.
- Give every empty state one primary next action:
  - Queue: **Add footage**
  - Library: **Search or select footage**
  - Collection: **Open in Paper Edit** or **Open in Storyline**
  - Paper Edit: **Add the first passage**
  - Storyline: **Add media** or **Open linked Paper Edit**

### Library and Collections

- Keep Library global and Collections scoped; selecting a Collection must not visually activate Library.
- After **Add to Collection**, show collection name, number added, duplicates skipped, and **Open collection**.
- Remember the last/recent collection in the picker without making the choice irreversible.
- Explain partial exports: exported count, offline/missing count, destination, and **Open folder**.
- Keep **Open results** and **Show in Explorer** prominent and consistently placed.
- Inside a Collection, remove redundant **Add to Collection**. Keep **Export collection**, **Add media**, **Open in Paper Edit**, and **Open in Storyline**.

### Feedback, recovery, and accessibility

- One notification pattern for success, partial success, recoverable failure, and blocking failure.
- Background tasks longer than roughly one second get progress and safe cancellation.
- Closing during indexing, export, or unsaved editing provides a specific choice.
- Visible autosave status and recovery after interrupted sessions.
- Logical keyboard focus, visible focus rings, accessible names, and sufficient contrast.
- Icon-only controls have tooltips and accessible labels; interactive targets are at least 32 px.
- Respect reduced-motion preferences; Transcape receives a calm/instant entrance option.
- Verify the complete primary journey without a mouse.

---

## P1 — Obvious performance work

1. **Debounce Paper Edit sync and autosave.** Avoid deep-copying/rebuilding the sequence on every keystroke.
2. **Incremental passage updates.** Recompute only the changed passage and affected downstream positions.
3. **Cache search indexes.** Normalize transcript and visual/object terms once per changed asset.
4. **Lazy thumbnails with a bounded cache.** Prioritize visible rows and cancel off-screen requests.
5. **Keep file work off the UI thread.** Indexing, copy, export, thumbnails, and graph preparation use cancellable worker jobs.
6. **Batch and atomically persist state.** Coalesce rapid edits, write a temporary state, then replace the last valid file.
7. **Release inactive media resources.** Stop/detach old preview sources when selection or view changes.
8. **Cache the Transcape graph.** Rebuild only when its data changes and enforce a node/edge budget.

Measure startup, search response, thumbnail appearance, typing latency, sync latency, timeline responsiveness, and export time against small, medium, and large fixture libraries.

---

## P1 — Code and app hygiene

“App hygiene” means the quiet fundamentals that make Tracer trustworthy, maintainable, and shippable—not only clean code.

### Architecture and code

- Keep this release surgical; do not rewrite the application shell.
- Extract the Paper sequence mapper/synchronizer and Storyline tool controller into focused modules.
- Move page-specific UI out of the oversized application module opportunistically as those areas are changed.
- Centralize design tokens, actions, shortcuts, terminology, and notifications.
- Add typed boundary models for Passage, Sequence, Track, Clip, Collection, and operation results.
- Replace broad exception swallowing in changed paths with specific errors and safe UI messages.
- Add formatting/lint checks and an incremental type check to the current test command.
- Remove legacy UI only after usage is proven absent; isolate compatibility readers.

### Data safety and diagnostics

- Version the saved-state schema; test migration from 1.19.2 and 1.20.
- Back up the last valid state before migration and expose recovery if loading fails.
- Add a rotating local diagnostic log that excludes transcript contents and redacts sensitive paths where practical.
- Add **Copy diagnostics** with version, platform, model state, task failures, and redacted paths.
- Validate export destinations and copied names; prevent traversal and accidental overwrite.
- Report partial success accurately rather than calling an entire operation successful.

### Product completeness

- About: SCG identity, Tracer version/build, license notices, local-processing/privacy statement, and diagnostics.
- Loading, empty, disabled, offline, partial, error, and complete states for every primary screen.
- Shortcut reference from Storyline and Help.
- Plain-language titles and confirmations; no implementation jargon.
- Defined, separate locations and cleanup behavior for user data, cache, models, logs, and installed files.

### Tests

- Retain current coverage and add behavior tests for stable passage IDs, diff sync, conflict preservation, shortcut focus, undo, and migration.
- Prefer user outcomes over tests coupled to widget structure or exact button labels.
- Add deterministic fixtures for transcript-only media, mixed media, missing media, and a manually edited linked sequence.
- Keep wide/narrow verification screenshots as visual evidence, not the only interaction proof.

---

## Delivery timeline

### Phase 0 — Freeze the baseline (half day)

- Let the other active editor finish and reconcile the worktree.
- Preserve 1.20 verification evidence.
- Run current tests and verification.
- Record representative performance timings and known failures.

**Gate:** one reproducible baseline with no unknown overlapping edits.

### Phase 1 — Shared sequence and Paper Edit (1–2 focused days)

- Add the stable passage model and migration.
- Implement diff synchronization and atomic revisions.
- Add passage affordances, timing controls, status, and undo.
- Prove persistence and preservation of Storyline-only work.

**Gate:** Paper Edit genuinely edits the linked spoken-story timeline.

### Phase 2 — Storyline tools and layout (1–2 focused days)

- Build the compact dock and shared shortcut/action registry.
- Complete Selection, Track Select, Ripple, Razor, Hand, and Zoom.
- Rework the sequence media panel and feedback states.
- Verify preview/playhead synchronization.

**Gate:** every shipped tool is understandable, keyboard-accessible, and complete.

### Phase 3 — Polish, hygiene, and performance (about 1 day)

- Complete terminology, empty states, feedback, recovery, accessibility, and diagnostics.
- Apply low-risk performance work.
- Add migration, failure, and interaction coverage.

**Gate:** no known P0/P1 issue in the primary journey.

### Phase 4 — Upgrade Pass and Ship Pass (half to one day)

- Re-run the full journey with interaction evidence.
- Review wide/narrow layouts and non-happy paths.
- Check secrets, unsafe file handling, dependencies/licenses, logs, recovery, and release metadata.
- Fix release blockers and document intentionally deferred issues.

**Gate:** release candidate approved for packaging.

### Phase 5 — Publish Tracer (half to one day, excluding certificate procurement)

- Produce the Windows installer and test it on a clean machine.
- Verify fresh install, 1.19.2 → current, 1.20 → current, and uninstall behavior.
- Confirm user data survives upgrade/uninstall unless explicitly removed.
- Apply code signing if available; otherwise use a clear internal/beta distribution warning.
- Generate checksum, release notes, known issues, and rollback instructions.
- Final smoke journey: install → add media → index → search → Collection → Paper Edit → Storyline → Premiere XML/project export.

**Gate:** distributable build, release notes, reproducible smoke test, and rollback path.

Estimated focused effort: **4–7 working days**, provided overlapping edits are reconciled before Phase 0. This is an effort range, not a calendar promise.

## Release acceptance checklist

- The complete primary journey works on a clean installation.
- Paper Edit and Storyline persist one linked spoken-story sequence.
- Manual Storyline layers survive Paper edits.
- All visible timeline tools and documented shortcuts work.
- Autosave, recovery, migration, partial export, offline media, and task failure are tested.
- UI works at 1100×720 and is polished at 1440×900.
- Keyboard-only traversal and focus behavior pass the primary journey.
- Logs contain no transcript content, credentials, or unredacted sensitive paths.
- No release-blocking crash, data loss, or silent failure remains.
- Installer, version metadata, checksum, release notes, and rollback instructions agree.

## Explicitly deferred larger ideas

These may be valuable later but should not delay publishing:

- full word-level transcript editing and phoneme-aware trims;
- unrestricted bidirectional merging between prose and every Storyline operation;
- Slip, Slide, Rolling Edit, Rate Stretch, keyframes, and other advanced trim tools;
- automatic B-roll placement or semantic scene construction;
- multicam and collaborative editing;
- plug-in/export ecosystem and automatic updater;
- broad application-shell rewrite.

## Recommended decision

Approve this as a **1.21 finishing release**, in this order:

1. linked timeline model and Paper Edit controls;
2. Storyline tool dock, shortcuts, and media panel;
3. journey polish, hygiene, and obvious performance work;
4. Upgrade Pass, Ship Pass, then publishing.

Do not begin the larger deferred ideas until the published primary journey is stable.

## Reference conventions

- Adobe Premiere tools: <https://helpx.adobe.com/nz/premiere/desktop/get-started/tour-the-workspace/tools-panel-and-options-panel.html>
- Adobe editing workflow and common shortcuts: <https://helpx.adobe.com/uk/premiere/desktop/edit-projects/intro-to-editing/edit-video-in-premiere.html>
- Adobe ripple editing: <https://helpx.adobe.com/sa_en/premiere/desktop/edit-projects/trim-clips/perform-ripple-edits.html>
- Adobe shortcut discovery: <https://helpx.adobe.com/premiere/desktop/get-started/keyboard-shortcuts/find-keyboard-shortcuts.html>
