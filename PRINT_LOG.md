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

## Vessel 2 — Tube Test Fits (`test_fits/tube.py`)

Iterating the top opening ID for the second vessel, the same way vessel 1's mouth was dialled in before the LED Sun Lid prototype settled it exactly. See `spec/vessel_2.md`.

| Date | Time (approx) | OD (mm) | Wall (mm) | Height (mm) | ID (mm) | Notes | Feedback |
|------|----------------|---------|-----------|--------------|---------|-------|----------|
| 2026-08-31 | 19:11 | 116 | 1 | 15 | 114 | First trial — caliper read 4.6in (116.84mm), rounded down. Not printed — superseded below before export. | |
| 2026-08-31 | 19:15 | 116 | 2 | 15 (+2 lip) | 112 | Wall increased 1 → 2mm. Added a 4mm-wide (0.16in = 4.064mm, rounded down) stop lip at the bottom, OD 124mm, 2mm tall, so the tube seats depth-controlled against the rim instead of sliding through. Superseded below before printing. | |
| 2026-08-31 | 19:17 | 116 | 2 | 10 (8 tube + 2 lip) | 112 | Overall height reduced 17 → 10mm; tube body shortened to 8mm, lip unchanged at 2mm. Superseded below before printing. | |
| 2026-08-31 | 19:18 | 116 | 2 | 10 (9 tube + 1 lip) | 112 | Lip thickness reduced 2 → 1mm; tube body grew to 9mm to hold overall height at 10mm. Printed. | Loose. |
| 2026-08-31 | 19:58 | 118 | 2 | 10 (9 tube + 1 lip) | 114 | OD stepped up 116 → 118 after the 116 print fit loose. Superseded below before printing. | |
| 2026-08-31 | 19:58 | 118 | 2 | 8 (7 tube + 1 lip) | 114 | Overall height reduced 10 → 8mm; tube body shortened to 7mm, lip unchanged at 1mm. Printed. | Fits — tighter end of good (reported 2026-09-01). Promoted `top_opening_id` to `spec/vessel_2.md`. |

## LED Sun Lid (`led_sun_lid/lid.py`)

| Date | Revision | Rim OD (mm) | Hub Bore (mm) | Notes | Feedback |
|------|----------|-------------|----------------|-------|----------|
| 2026-08-01 | 10.5mm-thickness | 167.0 | 89.5 | First full prototype | Fit absolutely perfectly (reported 2026-08-02) — both diameters now recorded as standard slip fits, see `spec/vessel.md` and `spec/led_ring_light.md` |

## Vessel Base Cradle (`test_fits/bowl.py`)

Cradle that the vessel base sits in — the inverse of `test_fits/base.py`. Floorless: the vessel rides on the lip that reaches in under its corner radius.

| Date | Time (approx) | Variant | Cavity OD (mm) | Corner R (mm) | Wall (mm) | Height (mm) | Notes | Feedback |
|------|----------------|---------|-----------------|----------------|-----------|--------------|-------|----------|
| 2026-08-07 | 18:15 | `ring_clipped`, one body | 181.0 | 5.5 | 3.6 | 12 | Full 188.2mm ring clipped to the 180mm bed, leaving four flats. Cradles a **trial** vessel base of OD 180 / corner R 5 with 0.5mm radial clearance — those base figures were unconfirmed guesses at the time. 21.6cm³. | |
| 2026-08-08 | 08:49 | `ring_clipped`, one body, floorless | 178.4 | 5.2 | 3.6 | 12 | The regressed design: 2mm floor and the constant-stiffness lobed opening both removed for print speed, vessel taken to 178 OD with the 0.2mm radial free fit. 23.8cm³, 180×180×12. At this diameter the flats keep 0.8mm of wall, so no wall sectors are dropped at all. | **Fits perfectly** (reported 2026-08-08). This is what confirmed the vessel base OD of 178 and corner radius of 5 — both moved into `spec/vessel.md` as confirmed on the strength of it. |

**Watch on the 2026-08-07 print:** at the four flats the upright wall was entirely gone across ±6°, and the ring was joined there only by the bottom lip web — 3.21mm tall, 27% of the 12mm section. Those webs were the expected failure point if it splayed. The four-segment alternative (`segments` in the same script) keeps full section everywhere and remains the stronger option. This does not apply to the 2026-08-08 print: at 178 the wall survives all the way round.

**Watch on the 2026-08-08 print:** with the floor gone the seat's inner lip meets z=0 tangentially at r=84, so it tapers out to nothing rather than standing on 2mm of floor. Expect stair-stepping on the first few layers at the bore, and treat that lip as the fragile part when handling it.

## Notes

- Exports at OD 169mm and OD 167mm (both 2mm wall, 10mm height, ~18:23–18:24 on 2026-08-01) were generated but **not printed** — omitted from this log by request.
- Confirmed component dimensions belong in `spec/` — one document per off-the-shelf component. Allowances between parts belong in `spec/fits.md`, not in either.
- A print fitting is what promotes a figure from a trial value in a script to a confirmed row in `spec/`. That is the main reason this log exists: it is the evidence behind those Confirmed dates.
- Since `output/*.step` folders are gitignored and overwritten on every run, this log is the only durable record of what dimensions were actually exported and tested — update it whenever a print is confirmed.
