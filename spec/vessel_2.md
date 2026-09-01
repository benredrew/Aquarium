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
| `top_opening` | Top opening | | | | | | Caliper read 4.6in on 2026-08-31, converted to 116.84mm and rounded down to 116mm. That 116 is only the first trial diameter for `test_fits/tube.py` — a caliper is awkward to seat squarely across a mouth opening, so this row stays unconfirmed until a printed ring actually fits, the same way vessel.md's `top_opening_id` was settled by the LED Sun Lid prototype rather than by the caliper reading that preceded it. |

## Notes

- Nothing else about this vessel is measured yet. This document is expected to fill in the same way `vessel.md` did: literals dialled in a test-fit script, promoted here only once a print (or a direct instrument reading) confirms them.
- The 116mm working estimate lives in `test_fits/tube.py` as `OD`, not here, until it is confirmed — see that file's log entry in `PRINT_LOG.md`.
