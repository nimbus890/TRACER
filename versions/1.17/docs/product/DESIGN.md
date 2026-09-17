# Tracer interface direction

## 1.17 refinement

This release keeps the approved Modular Desk palette and hierarchy. Search provenance is communicated with tiny unboxed glyphs rather than additional badges. Processing mode uses a compact two-part segmented control. Timeline zoom does not retain a decorative focus rectangle, while keyboard focus remains available elsewhere. The left rail footer contains only the quiet GPU, VRAM, and RAM meters and the Tracer version; redundant local/offline copy is removed.

## Current 1.16 direction

The selected Modular Desk concept governs this release: a precise graphite desktop workspace with the transcript or timeline dominant, compact neutral panel headers, small opaque symbols, and restrained orange selections.

The current tokens supersede the older palette below: app #14181b, sidebar #101417, work surface #171c20, panel header #1b2126, structural border #303940, text #dce1e5, secondary #9aa6ae, primary #e68b4f, focus #659ed3. Navigation is 76 px wide with 18 px icons. Panel headers expose a drag grip, focus control, and overflow menu. Native dock dividers are 6 px and highlight on hover.

Reference: Penpot's GitHub workspace and top_toolbar.cljs, studied for grouped tools, explicit active states and contextual chrome. Implementation is original Qt code; the selected generated image is a visual reference rather than a specification of unsupported features.

Paper Edit has three useful arrangements: writing with a transcript-source rail, search with a persistent adjacent result panel, and a vertically ordered passage panel. Preview and reference panels stack at the side. Storyline owns its timeline. Title duplication and toolbar density should continue to be reduced in later refinement without removing useful labels.

Final 1.16 QA: rendered full and narrow Paper Edit/Find, offline/no-match, passage order, Library, and Storyline with export dock. Full-size screenshots use 1440×900; narrow acceptance asserts an actual 1100 px window without forcing a wider minimum. Native Windows preview playback was checked.

## Direction

Tracer should feel like a focused dark editing desk: calm, precise, and made for long sessions. The user's footage, transcript, and sequence dominate; application chrome recedes. Orange signals Tracer identity and primary action, amber marks editorial emphasis, red belongs to handwritten annotation or danger, and blue is reserved for genuine informational states.

## Principles

- Keep professional density, but give every region unequal visual weight.
- Let the work surface dominate; avoid decorative cards, gradients, glass, and blur.
- Reuse one compact icon language with visible labels for navigation and tooltips for unfamiliar actions.
- Preserve writer-specific typography in Paper Edit without turning it into a separate product.
- Use color semantically and sparingly. Neutral gray is structural, not decoration.
- Prefer direct manipulation, persistent context, and reversible actions.

## References

- Adobe Premiere Pro: quiet professional panels and stable editing muscle memory. Borrow density and tool hierarchy, not its exact layout.
- Scrivener: manuscript-first attention and restrained supporting chrome. Borrow the writing focus, not its document-management complexity.
- Adobe Spectrum and Microsoft Fluent: accessible control states, platform familiarity, focus visibility, and compact desktop targets.

## Layout and hierarchy

- The 92 px navigation rail is stable across workspaces.
- Paper Edit uses three resizable regions: transcript sources, the dominant script, and source/visual reference context.
- The script remains the widest and highest-contrast content surface.
- The Paper Sequence stays attached beneath the script as a compact reorder strip.
- At narrower desktop sizes, panels compress without hiding the transcript or moving primary actions.

## Core tokens

- App background: #151515
- Raised work surface: #1d1d1c
- Inset content surface: #191919
- Structural border: #34322f
- Primary text: #e8e3da
- Secondary text: #99958e
- Tracer accent / section label: #d78061
- Primary action: #c86f50 with #16120f text
- Editorial marker: #443820 surface with #b88a31 border
- Handwritten annotation: #e47b61
- Selection: #483128 with #fff5ee text

## Component and state rules

- Primary buttons use solid orange; toolbar buttons use neutral raised surfaces.
- Hover increases border contrast without glow or layout movement.
- Selected tools use the dark amber editorial state, not the primary-action orange.
- Search matches use a dark warm highlight so text remains legible.
- Disabled controls retain their shape but recede below secondary text.
- Pen and marker annotations remain visually distinct from selection and search.
- Empty Paper Edit keeps the same three-region frame and presents Library as the clear next action.

## Accessibility and platform behavior

- Keep body text and active controls at readable contrast on the dark surfaces.
- Every icon-only action needs an accessible name or tooltip.
- Keyboard focus must remain visible; drag interactions retain button or command alternatives.
- Native Windows media dialogs are used for familiar navigation and DPI behavior.
- Per-monitor DPI awareness and 2x rendered icons protect sharpness.

## Visual QA

## Full-stack upgrade

Passage editors fit their text between 62 and 300 px so short quotes do not become large empty panels. The search field retains 220 px minimum width; repeated-term detail moves to a tooltip. Existing dark palette and manuscript hierarchy are preserved. The Library chooser's Add count includes checked results hidden by the current search.

- Inspect Paper Edit populated at 1280×860 and 1100×720.
- Inspect the empty transcript state.
- Check selected marker, freehand pen, search match, disabled, hover, and primary-action states.
- Confirm no stale transcript rows overlap after switching or refreshing documents.
