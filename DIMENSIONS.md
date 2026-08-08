<!--
Author: Claude (Sonnet 5)
Co-Author: Brendan Fennell
-->
# Vessel Dimensions

Confirmed measurements of the physical aquarium (1-gallon glass vessel, stacked series of cylinder diameters). Only record values that have been measured/verified — not test-fit or trial dimensions used in scripts.

## Stacked Sections

List sections from bottom to top (or top to bottom — pick one and stay consistent).

| Section | OD (mm) | Wall (mm) | ID (mm) | Height (mm) | Notes |
|---------|---------|-----------|---------|-------------|-------|
| Top opening |     |           | 167     |             | Confirmed 2026-08-01. Drives the outer diameter of the LED Sun Lid. |

## Fit conventions

- **Free fit on a vertical wall: 0.2mm radial.** A bore comes out 0.4mm over the shaft it takes. This is the default for any sliding or drop-in joint between vertical faces — the lid/screen joint uses it (`led_sun_lid/lid.py`, `SCREEN_CLEARANCE`) and so does the vessel cradle (`test_fits/bowl.py`, `CLEARANCE`). Confirmed as the house figure 2026-08-07; earlier cradle trials used 0.5mm radial, which is why the first printed cradle engraved a bore of 181 for a 180 vessel.
- Clearance applies to **walls only**. Faces normal to Z are left tight where a part is meant to bed down or finish flush — see the screen lip sitting in the lid's rebate.
- A slip fit into the vessel mouth is a separate case and takes **no** added clearance: see the standard slip-fit OD below.

## Notes

- Top ID of 167mm is the reference dimension for any part that seats into the vessel mouth.
- **Standard slip-fit OD: 167.0mm.** Confirmed 2026-08-02 via the LED Sun Lid prototype (10.5mm-thickness revision, printed 2026-08-01) — its rim OD is set directly to this ID with no additional clearance, and fit perfectly. Use 167.0mm as the default outer diameter for any future part seating in the vessel mouth.
