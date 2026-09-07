<!--
Author: Claude (Sonnet 5)
Co-Author: Brendan Fennell
-->
# Vessel 2 — Specifications

Confirmed dimensions of the second physical aquarium vessel. Kept in its own
document, separate from [vessel.md](vessel.md), so the two vessels can use the
same row and column keys — `top_opening_id`, `base_od` — without colliding;
`specs.figure` is addressed by document and key together for exactly this
reason.

A figure belongs here once it is confirmed, either by caliper or by a printed
part that fits; the Notes say which. Figures still being dialled in stay as
literals in the script that is dialling them, and move here when they settle.

Allowances laid on top of these figures are **not** here — see [fits.md](fits.md).

## Stacked Sections

Rows are keyed the same way as `vessel.md`: `specs.figure("vessel_2", "top_opening_id")`.

| Key | Section | OD (mm) | Wall (mm) | ID (mm) | Height (mm) | Corner radius (mm) | Notes |
|-----|---------|---------|-----------|---------|-------------|--------------------|-------|
| `top_opening` | Top opening | | | 118 | | | Confirmed 2026-09-01 by `test_fits/tube.py` (118mm OD, 2mm wall, 8mm overall height) seating in it — reported "tighter end of good," not loose. Walked up from a 116mm caliper-derived first trial, which printed loose. Worth a caliper cross-check against the mouth directly at some point, since 118 sits without margin. |

## Notes

- Nothing else about this vessel is measured yet. This document is expected to fill in the same way `vessel.md` did: literals dialled in a test-fit script, promoted here only once a print (or a direct instrument reading) confirms them.
- The **top opening ID of 118mm** is the reference dimension for anything seating into this vessel's mouth, the same role `top_opening_id` plays in `vessel.md`. Read it via `specs.figure("vessel_2", "top_opening_id")` rather than retyping 118.
- It fit on the tighter end of good rather than with margin — a part designed to seat here should probably not assume the 0.2mm free fit used elsewhere (see [fits.md](fits.md)) unless retested.
