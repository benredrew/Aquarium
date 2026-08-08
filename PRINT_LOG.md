<!--
Author: Claude (Sonnet 5)
Co-Author: Brendan Fennell
-->
# Print Log

Record of parts actually printed and tested against the vessel. Only confirmed prints belong here — see notes below for exports that were generated but skipped.

## Tube Test Fits (`test_fits/tube.py`)

| Date | Time (approx) | OD (mm) | Wall (mm) | Height (mm) | ID (mm) | Notes | Feedback |
|------|----------------|---------|-----------|--------------|---------|-------|----------|
| 2026-08-01 | 16:23 | 180 | 2 | 10 | 176 | First export, initial baseline dimensions | |
| 2026-08-01 | 16:26 | 180 | 2 | 10 | 176 | Re-export after wiring up the live viewer (`set_port` fix); same dimensions as above | |
| 2026-08-01 | 16:33 | 180 | 2 | 10 | 176 | Re-export after relocating script into `test_fits/` folder structure; same dimensions as above | |
| 2026-08-01 | 17:40 | 168 | 2 | 10 | 164 | OD reduced from 180 to 168 (via intermediate 170/166mm trials at 5mm height, not logged here since not printed at that height) | |

## LED Sun Lid (`led_sun_lid/lid.py`)

| Date | Revision | Rim OD (mm) | Hub Bore (mm) | Notes | Feedback |
|------|----------|-------------|----------------|-------|----------|
| 2026-08-01 | 10.5mm-thickness | 167.0 | 89.5 | First full prototype | Fit absolutely perfectly (reported 2026-08-02) — both diameters now recorded as standard slip fits, see `DIMENSIONS.md` and `LED_RING_LIGHT.md` |

## Vessel Base Cradle (`test_fits/bowl.py`)

Cradle that the vessel base sits in — the inverse of `test_fits/base.py`. Floorless: the vessel rides on the lip that reaches in under its corner radius.

| Date | Time (approx) | Variant | Cavity OD (mm) | Corner R (mm) | Wall (mm) | Height (mm) | Notes | Feedback |
|------|----------------|---------|-----------------|----------------|-----------|--------------|-------|----------|
| 2026-08-07 | 18:15 | `ring_clipped`, one body | 181.0 | 5.5 | 3.6 | 12 | Full 188.2mm ring clipped to the 180mm bed, leaving four flats. Cradles a **trial** vessel base of OD 180 / corner R 5 with 0.5mm radial clearance — those base figures are unconfirmed guesses, not measurements. 21.6cm³. | |

**Watch on this print:** at the four flats the upright wall is entirely gone across ±6°, and the ring is joined there only by the bottom lip web — 3.21mm tall, 27% of the 12mm section. Expect those webs to be the failure point if it splays. The four-segment alternative (`segments` in the same script) keeps full section everywhere and is the stronger option if this cracks.

## Notes

- Exports at OD 169mm and OD 167mm (both 2mm wall, 10mm height, ~18:23–18:24 on 2026-08-01) were generated but **not printed** — omitted from this log by request.
- Confirmed vessel measurements (not test-fit trial values) belong in `DIMENSIONS.md`.
- Since `output/*.step` folders are gitignored and overwritten on every run, this log is the only durable record of what dimensions were actually exported and tested — update it whenever a print is confirmed.
