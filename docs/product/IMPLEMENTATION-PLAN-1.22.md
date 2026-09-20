# Tracer 1.22 — Feature Completion, App Finishing & Publishing Plan

**Status:** Proposed; approval required before implementation.  
**Baseline:** Review and build from the completed `versions/1.21` snapshot, not from the older 1.20 root files.  
**Release intent:** Correct and finish the two editing improvements introduced in 1.21, then spend most of the release debugging and polishing the existing app.

## Scope balance

- **30% — targeted feature completion:** Paper Edit/Storyline linkage and visual Storyline controls/shortcuts.
- **70% — finishing:** regressions, interaction quality, consistency, states, accessibility, performance, reliability, tests, packaging, and publishing.

1.22 is not a product rethink and should not add another major workflow.

## 1.21 critique

### Keep and build on

- Stable passage identities linking manuscript passages to timeline clips.
- Preservation of B-roll and additional audio tracks during Paper Edit synchronization.
- Text-focus guard for timeline shortcuts.
- Migration path and backup from earlier saved state.
- Diagnostic path redaction.
- Wide and narrow screenshot verification.
- Familiar Premiere shortcut choices where Tracer already supports the same action.

### Correct in 1.22

1. **The release evidence is inaccurate.** The 1.21 release note says 60 tests pass. Running the snapshot produced 60 tests with two Paper Edit regression failures and one skip. The visual journey verifier passes, but that does not cancel the regressions.
2. **The tool dock does not meet the visual brief.** The six tools are represented by letter buttons (`V A B C H Z`), not meaningful symbols. They require prior shortcut knowledge and do not improve recognition for a new viewer.
3. **Several new tools are weakly verified.** The verifier exercises Razor, but only confirms that Track Select and Ripple can be selected; it does not prove their real editing behavior. Hand and Zoom are similarly not behavior-tested.
4. **Paper Edit became more control-heavy.** Persistent sync text, timing badges, instructions, Trim, Split, and source actions compete with the document. The original brief was for a document that also drives a timeline, not a technical transcript editor.
5. **The sync guarantee needs stronger proof.** The new synchronizer reconstructs the spoken V1/A1 clip lists while preserving other tracks. This may be acceptable, but overlap behavior, edits on V1/A1, active-document assumptions, undo, and repeated synchronization need realistic tests before claiming complete preservation.
6. **Storyline-to-Paper trim synchronization is context-dependent.** The current UI updates Paper Edit only when the relevant document is already active in the Paper Edit page. Opening or trimming a linked sequence directly must resolve its document by ID instead of relying on current page state.
7. **Some additions are unused or over-specified.** Dialogue-handle logic exists but is not part of the actual synchronization path. Estimated split timing introduces complexity that is not required to finish the current product.

### 1.22 decision

Retain the sound underlying work from 1.21, remove or simplify anything that distracts from the document, verify every timeline tool before showing it, and make the rest of the release an app-wide finishing pass.

---

## Part A — Finish the two editing improvements

## A1. Paper Edit and Storyline connection

### Product rule

Paper Edit remains a writing surface. Its existing passage order and included/excluded state define the spoken-story assembly in the linked Storyline sequence. Storyline remains the visual finishing surface.

### Work

- Fix both existing Paper Edit regression tests before changing behavior.
- Keep the stable passage IDs and linked sequence introduced in 1.21.
- Ensure passage reorder and include/exclude update the linked speech clips deterministically.
- Keep ordinary wording edits from deleting, duplicating, or retiming media.
- Resolve a linked Paper Edit document through `paper_document_id`, even if that document is not currently open.
- Preserve Storyline-only tracks and validate what happens to manual clips placed on the primary speech tracks.
- Debounce document synchronization and skip timeline work when only non-timeline text changed.
- Prevent repeated sync from creating duplicates or changing stable clip IDs.
- Make manual-cut preservation explicit and understandable instead of silently producing a similarly named sequence.
- Ensure Paper Edit and Storyline exports use the same speech order.

### UI simplification

- Keep the clean document, search/source layout, source preview, and existing Passage Order view.
- Reduce the permanent instructional sentence and technical timing language.
- Use one quiet linkage state: **Updating**, **Linked**, or **Needs review**.
- Reveal passage timing/source actions only on selection or context menu.
- Keep Trim only if it is reliable and understandable; otherwise defer it rather than shipping an exposed seconds-only dialog.
- Keep Split only if it can preserve source identity, undo correctly, and survive reload. Otherwise hide it for 1.22.
- Make included/excluded passages visually clear without adding a permanent control rail.
- **Open in Storyline** must always reveal the exact linked sequence.

### Required proof

- Edit wording, delete wording, undo, reorder, exclude, restore, copy/paste, switch documents, restart, and export.
- Repeat synchronization several times and confirm stable identities and no duplicates.
- Add B-roll/audio and manually edit clips before Paper changes; confirm what is preserved.
- Trim a linked clip after opening Storyline directly; confirm the correct Paper document updates.
- Test offline source media without losing manuscript state.

## A2. Storyline visual tools and shortcuts

### Visual correction

- Replace the `V A B C H Z` letter buttons with recognizable monochrome symbols:
  - pointer for Selection;
  - pointer/stack or forward-track mark for Track Select;
  - opposing trim arrows for Ripple;
  - razor blade for Cut;
  - hand for Pan;
  - magnifier for Zoom.
- Keep the shortcut visible in the tooltip, not as the primary button artwork.
- Use one icon size, button size, stroke weight, active color, hover state, focus state, disabled state, and spacing system.
- Group editing modes, edit commands, track actions, and view controls clearly without spreading them into unrelated rows.
- Keep accessible names and a visible keyboard-focus treatment.

### Shortcut set

Retain shortcuts only for supported and tested behavior:

| Existing action | Shortcut |
|---|---:|
| Selection | `V` |
| Track Select Forward | `A` |
| Ripple Edit | `B` |
| Razor | `C` |
| Hand/Pan | `H` |
| Zoom | `Z` |
| Play/pause | `Space` |
| Step one frame | `Left` / `Right` |
| Previous/next edit | `Up` / `Down` |
| Split at playhead | `Ctrl+K` |
| Undo/redo | `Ctrl+Z` / `Ctrl+Shift+Z` |
| Copy/paste | `Ctrl+C` / `Ctrl+V` |
| Delete/ripple delete | `Delete` / `Shift+Delete` |
| Zoom in/out | `=` / `-` |

### Behavior gate

Each tool must pass interaction tests, not only existence checks. If Track Select, Ripple, Hand, or Zoom cannot pass the gate without enlarging the release, hide that tool and keep the proven subset. A smaller trustworthy dock is better than six partly working controls.

Required checks:

- correct pointer and active state;
- click/drag behavior at different zoom levels;
- locked and disabled tracks;
- linked A/V clips;
- undo and redo;
- playhead/preview synchronization;
- text-input shortcut guard;
- no accidental shortcuts outside Storyline.

### Existing sequence media panel

Do not redesign the panel. Refine its current layout:

- improve row density and name/duration hierarchy;
- make drag and insert behavior discoverable;
- clarify selected, loading, empty, no-results, missing-media, and error states;
- preserve useful timeline width at 1100×720;
- remove redundant instructional text after the first successful use.

---

## Part B — Finish the current app

## B1. Primary journey regression pass

Exercise the complete current journey from both empty state and an upgraded library:

> Queue → Library → Collection → Paper Edit → Storyline → Export

For every transition check current location, primary next action, cancel/back behavior, undo, progress, success, failure, recovery, persistence, and restart.

## B2. Screen-by-screen work

### Queue

- Verify add, process, pause/cancel if supported, retry, duplicates, missing files, progress, failure, completion, and restart recovery.
- Disable unavailable actions and remove stale instructions or debug copy.

### Library

- Verify search across transcript, filename, visual/object terms, and active filters.
- Improve filter clarity, selection feedback, add-to-Collection completion, duplicate handling, preview tabs, search highlighting, frames, metadata, offline media, **Open results**, and **Show in Explorer**.
- Confirm global Library has no project export action.

### Collections

- Keep Collection navigation independent from Library selection.
- Remove remaining user-facing “Project” language except **Export as Project**.
- Verify add/remove media, Paper Edit, Storyline, empty/offline state, export report, and **Open folder**.
- Remove redundant add-to-Collection actions inside a Collection.

### Paper Edit

- Complete Part A1.
- Refine page width, typography, paragraph rhythm, selected/excluded treatment, search results, source preview hierarchy, focus, annotations, and export feedback.
- Remove anything added in 1.21 that makes the page feel less like a document without delivering reliable editing value.

### Storyline

- Complete Part A2.
- Refine the existing sequence tabs, preview, timeline, track headers, selected clip, status text, media panel, and export area as one composition.
- Fix cramped layout and disabled/no-op actions before changing the overall architecture.

### Transcape

- Preserve its Easter-egg role and existing data model.
- Verify entry/exit, pan, zoom, focus, source opening, empty data, bounded graph size, performance, reduced motion, and return to the previous workspace.
- Add no new visualization modes.

### Settings and shell

- Verify version/build, paths, model state, validation, persistence, sidebar state, breadcrumbs, dialogs, resize/minimum size, focus return, and SCG/Tracer branding.
- Remove dead buttons, inconsistent capitalization, debug language, and stale terminology.

## B3. Visual and interaction consistency

- Normalize typography, spacing, row height, dividers, icon weight, button hierarchy, and panel density.
- Audit hover, focus, active, selected, disabled, loading, empty, partial, error, and success states.
- Use at least 32 px interaction targets, visible focus, sensible tab order, accessible names, readable contrast, and reduced motion.
- Preserve the approved neutral visual direction; no decorative redesign for novelty.

## B4. Reliability, performance, and app hygiene

- Verify autosave covers every existing user-changing action.
- Surface save, indexing, preview, synchronization, and export failures.
- Test migration and recovery from 1.19.2, 1.20, and 1.21.
- Keep missing media non-destructive.
- Prevent duplicate collection membership, linked sequences, and export filename collisions.
- Debounce Paper sync and cache normalized search terms.
- Lazy-load visible thumbnails and cap caches.
- Keep indexing, thumbnails, copying, and export off the UI thread.
- Coalesce and atomically write state.
- Release inactive media resources.
- Cache Transcape until its source data changes.
- Centralize Storyline actions so icon, shortcut, tooltip, enabled state, and command cannot disagree.
- Limit refactoring to changed or demonstrably risky code.
- Check packaged files for secrets, debug artifacts, private paths, and transcript content in logs.
- Verify dependencies, licenses, version metadata, and release notes.

---

## Implementation order

### Phase 0 — Adopt and verify 1.21

- Treat `versions/1.21` as the candidate baseline.
- Preserve the current 1.20 root until 1.21 behavior and state migration are understood.
- Reproduce the two failing regression tests and the passing visual verifier.
- Record which 1.21 claims are proven, partial, or unproven.

**Exit:** a trustworthy 1.21 baseline for 1.22 work.

### Phase 1 — Correct the editing features

- Fix Paper Edit regressions and synchronization context/preservation problems.
- Simplify the Paper UI back toward a document.
- Replace letter buttons with symbols.
- Exercise and repair each current tool and shortcut; hide any tool that cannot meet the behavior gate.

**Exit:** the two requested editing improvements are complete and defensible.

### Phase 2 — Whole-app finishing pass

- Run the primary journey and every screen checklist.
- Correct broken, confusing, inconsistent, cramped, inaccessible, or silent behavior.
- Verify 1100×720 and 1440×900, plus important empty/offline/error states.

**Exit:** no known release-blocking defect and no avoidable major friction in the core journey.

### Phase 3 — Optimization and hygiene

- Apply only measured or obvious low-risk optimizations.
- Add focused regression tests and clean changed/risky paths.
- Re-run persistence, migration, export, privacy, and recovery checks.

**Exit:** responsive representative use and reproducible verification.

### Phase 4 — Ship Pass and publish

- Build the 1.22 release candidate.
- Test fresh install, 1.19.2/1.20/1.21 upgrade, restart, and uninstall behavior.
- Verify installer contents, version labels, licenses, checksum, release notes, known issues, and rollback instructions.
- Test the installer on a clean Windows environment.
- Sign if a certificate is available; otherwise identify the build clearly as unsigned beta/internal distribution.

**Exit:** publishable installer with a repeatable smoke test and rollback path.

## Estimated effort

- Phase 0: half day.
- Phase 1: 1–2 focused days.
- Phase 2: 1–2 focused days.
- Phase 3: half to one day.
- Phase 4: half to one day, excluding certificate procurement.

**Total:** approximately 3.5–6 working days. Scope freezes after Phase 1; defects and polish take priority over additional functionality.

## 1.22 release acceptance

- The complete Queue → Library → Collection → Paper Edit → Storyline → Export journey works on a packaged build.
- All tests pass; skips and unverified paths are disclosed rather than counted as passes.
- Paper Edit order/inclusion reliably drives the linked sequence without ordinary wording edits damaging media.
- Storyline edits resolve and update the correct linked Paper document.
- Manual Storyline work is preserved according to documented, tested rules.
- The timeline dock is symbol-led, understandable, accessible, and behavior-tested.
- Search, preview, Collections, export, Settings, and Transcape pass intended current journeys.
- Loading, empty, offline, partial, error, cancel, and recovery states are understandable.
- UI is usable at 1100×720 and polished at 1440×900.
- No known crash, data-loss, silent-failure, secret, or sensitive-log issue remains.
- Installer, app version, documentation, checksum, and release notes agree.

## Approval decision

Build **Tracer 1.22** from the reviewed 1.21 snapshot. Correct and finish its Paper Edit/Storyline work and visual timeline controls first. Then freeze feature scope and devote the remainder to debugging, refinement, optimization, verification, and publishing.

## Shortcut references

- Adobe Premiere tools: <https://helpx.adobe.com/nz/premiere/desktop/get-started/tour-the-workspace/tools-panel-and-options-panel.html>
- Adobe editing workflow and shortcuts: <https://helpx.adobe.com/uk/premiere/desktop/edit-projects/intro-to-editing/edit-video-in-premiere.html>
- Adobe shortcut discovery: <https://helpx.adobe.com/premiere/desktop/get-started/keyboard-shortcuts/find-keyboard-shortcuts.html>
