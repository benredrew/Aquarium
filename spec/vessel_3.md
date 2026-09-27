<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Vessel 3 — Specifications

Dimensions of the third physical aquarium vessel. Saved as from
[vessel_2.md](vessel_2.md) and kept in its own document for the same reason
that one is separate from [vessel.md](vessel.md): the three vessels use the
same row and column keys — `top_opening_id`, `base_od` — without colliding,
because `specs.figure` is addressed by document and key together.

A figure belongs here once it is confirmed, either by caliper or by a printed
part that fits; the Notes say which. Figures still being dialled in stay as
literals in the script that is dialling them, and move here when they settle.

Allowances laid on top of these figures are **not** here — see [fits.md](fits.md).

## Stacked Sections

Rows are keyed the same way as `vessel.md`: `specs.figure("vessel_3", "top_opening_id")`.

| Key | Section | OD (mm) | Wall (mm) | ID (mm) | Height (mm) | Corner radius (mm) | Notes |
|-----|---------|---------|-----------|---------|-------------|--------------------|-------|
| `top_opening` | Top opening | | | 112 | | | Given by Brendan 2026-09-10 when this vessel was opened. **How it was arrived at is not recorded here** — unlike Vessel 2's 118, no test-fit print or caliper reading backs it yet. Treat it as the working figure, not a confirmed one, until a part is offered up; then say here which it was. |

## Notes

- Nothing else about this vessel is measured yet. This document is expected to fill in the same way `vessel.md` did: literals dialled in a test-fit script, promoted here only once a print (or a direct instrument reading) confirms them.
- The **top opening ID of 112mm** is the reference dimension for anything seating into this vessel's mouth, the same role `top_opening_id` plays in `vessel.md` and `vessel_2.md`. Read it via `specs.figure("vessel_3", "top_opening_id")` rather than retyping 112.
- Vessel 2's mouth took `vessel_mouth_radial` = 0 and came out "tighter end of good". Whether that carries over is unknown while 112 itself is unconfirmed — the first part to seat here is doing two jobs at once, checking the allowance and checking the diameter, and a bad fit will not say which was wrong. `test_fits/tube.py` at 112 would separate them for the cost of one small print.
- Vessel 3 lid models depend on **LED Ring Light 2** (`led_ring_light_2.md`), as Vessel 2's do.
