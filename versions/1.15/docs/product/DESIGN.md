# Tracer interface direction

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
