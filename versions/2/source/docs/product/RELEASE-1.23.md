# Tracer 1.23 — Polish & Finishing

Direction: Polish the existing application, introduce beta feature gating, rebuild the Transcape visualization, and refine the core editing experience UI/UX.

## Beta toggle & gating

- Added a Beta feature toggle positioned immediately beside the Beta flask icon in the sidebar.
- Defaults to off and persists across sessions.
- When off, Paper Edit and Visual Indexing are hidden throughout the app, and the library picker subtitle is adjusted accordingly.

## Transcape rebuild

- Double-clicking the Tracer icon or wordmark opens Transcape.
- Rebuilt with force-directed physics layout, data-weighted node sizes, and cluster seeding.
- Features fluid motion, cursor repulsion, proximity labels, middle-mouse panning, and wheel zoom.
- Includes spatial reveal, direct node manipulation, Esc-to-exit, and frameless HUD chrome.

## UI refinements

- **Library splitter:** Video preview separated from transcript/frames/details with a resizable splitter.
- **Storyline collections & views:** Sequence Media uses a Select Collection dropdown, collection thumbnails, and a bottom-right tiny toggle switch between List and Grid views.
- **Track controls:** Hide/mute and lock vector options are rendered directly on each track header with click toggling, without button bounding boxes.
- **Storyline toolbar:** Edit tools sit compactly on the left, with Snap, Fit complete sequence, and the Zoom slider right-aligned.
- **Paper edit sheet:** Restyled as a clean document-like sheet centered in its scroll area.
- **Processing overlay:** Styled with a translucent dark scrim backdrop (`rgba(8, 10, 12, 195)`), opaque `#141414` card, reliable outside-click dismissal, and cursor glow.
- **Cursor aura:** Uses the exact Transcape glow formula (`radius=150`) strictly confined inside the sidebar and overlay, eliminating viewport aura and menu bar edge leakage.
- **Queue Add Media:** Interaction made more noticeable.

## Timeline shortcut improvements

- Improved shortcuts for Delete, ripple-delete, split, playback, clipboard, undo, and redo.
- Added Ctrl+Y for redo.

## Bug fixes

- Fixed transcape `seed_layout` infinite loop, O(N²) tick loop, and removed dead code.
- Cleaned unused imports in `transcape.py` and `timeline_tools.py`.

## Verification

- 73 automated tests pass; one existing environment-dependent test is skipped (total 74 tests).
- `verify_123.py` exercises the primary UI journey and renders Queue, Library, Collection, Paper Edit, Storyline, Transcape, narrow layouts, offline media, and empty Library states.
- Rendered screenshots are stored under `verification/1.23/`.
- The final standalone Windows build completes successfully at `dist/Tracer/Tracer.exe`; its SHA-256 is `6AAA94A0BE1EBB7CA67D92738E2864CF6C5C9448FD52CAAF653FA22EBCBEBC7A`.
- The standalone package includes the bundled `1.23` version metadata, Tiny model, and Visual Index model.

## Boundaries

- Focus remains on polishing the existing feature set and ensuring stability.
- Experimental features (Paper Edit, Visual Indexing) are safely gated behind the Beta toggle to protect the core editing experience.
