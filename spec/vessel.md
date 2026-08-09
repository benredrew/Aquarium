<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Vessel — Specifications

Confirmed dimensions of the physical aquarium: a 1-gallon glass vessel, a stacked series of cylinder diameters. It is an off-the-shelf component, so nothing here is a design choice — it is what the glass is.

A figure belongs here once it is confirmed, either by caliper or by a printed part that fits; the Notes say which. Figures still being dialled in stay as literals in the script that is dialling them, and move here when they settle.

Allowances laid on top of these figures — clearances, slip fits — are **not** here. They are in [fits.md](fits.md), because an allowance is a property of the joint, not of the glass.

## Stacked Sections

Sections from top to bottom.

Rows are keyed so the scripts can read them: `specs.figure("vessel", "top_opening_id")` returns the ID cell of the `top_opening` row. A figure is named for its row and its column, so one row carries a section's OD, wall, ID, height and corner radius as each gets confirmed, without needing a line per number. Leave the key off a row and the row is prose only.

| Key | Section | OD (mm) | Wall (mm) | ID (mm) | Height (mm) | Corner radius (mm) | Notes |
|-----|---------|---------|-----------|---------|-------------|--------------------|-------|
| `top_opening` | Top opening | | | 167 | | | Confirmed 2026-08-01 by the LED Sun Lid prototype seating in it. Drives the lid's rim OD. |
| `base` | Base | 178 | | | | 8 | OD confirmed 2026-08-08 by the floorless cradle printed that morning — cut for a 178 base with the 0.4mm diametral free fit, giving a 178.4 bore, and it fitted perfectly (superseded OD trials: 180, 177, 179). Corner radius settled 2026-08-08 by holding 45° section prints against the glass and comparing the curve directly (`test_fits/cradle_segment.py`); 5 and 7 were tried, 8 is the match. Established by eye, not by caliper. |

## The full exterior profile

The whole outside of the vessel — five outer diameters, their blends, and the R8 base roll — is modelled in `vessel/vessel.py`, which is the definition. The numbers are **not repeated here on purpose**: they are photo-derived, this document holds confirmed figures, and a second copy would drift from the first within a week.

What that model rests on: the two rows above (both confirmed), and everything else scaled from one photograph by the base OD. Diameters are good to a percent or two; the lower waist is the weakest part, because the substrate line crosses it in the picture. Locked in 2026-08-08 as good enough to design against — not as measurement.

## Notes

- The **top ID of 167mm** is the reference dimension for anything seating into the vessel mouth. It is keyed `top_opening_id` — read it rather than retyping 167. Note that a part seating there takes *no* added clearance; see [fits.md](fits.md).
- The **base OD and corner radius** are what `test_fits/base.py` models and what `test_fits/bowl.py` cuts its cradle cavity from. base.py reads both from this table and bowl.py derives from base.py, so the chain runs document → vessel model → cradle and the diameter is edited in exactly one place.
- **The two base figures rest on different evidence.** The cradle print confirmed the *diameter*: a 178.4 bore that fits is direct evidence about 178. It said nothing useful about the corner radius, because the vessel drops onto the seat and stops over a range of curvatures without the error being visible or felt — which is why the radius was settled separately, by printing 45° sections of the cradle and holding them against the glass to compare the curve. That is a visual match, good enough to design against but not a caliper reading. Neither figure has been measured directly.
- **The vessel's height has never been established.** `test_fits/base.py` assumes the tank is as tall as it is wide purely so `assembly.py` can place the lid at a plausible height. That assumption is not a figure and is deliberately absent from the table above — do not read it as one.
