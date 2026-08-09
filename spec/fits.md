<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Fits — Allowances

What to add, and to which face, when one part has to go into another. The component documents in this folder record what things *are*; this one records what to leave between them.

Every figure below is **radial** — the gap on one side. A bore takes twice it: the 0.2mm free fit puts a 0.4mm bore over the shaft it receives. Radial is the figure kept because it is the one that describes the gap you can actually see at any single point of contact; the diametral consequence follows from it, never the other way round.

## The rule that catches people out

An allowance applies to **walls only** — faces the part slides along on its way in. Faces normal to Z are left tight, because a part is meant to bed down or finish flush on them, and a gap there becomes a rattle rather than a fit. The screen lip sitting in the lid's rebate is the worked example: clearance on the lip's vertical edges, none under it.

## Allowances

| Key | Fit | Value (mm) | Confirmed | Notes |
|-----|-----|------------|-----------|-------|
| `free_wall_radial` | Free fit on a vertical wall | 0.2 | 2026-08-07, and again 2026-08-08 by the cradle | The house default for any sliding or drop-in joint between vertical faces. Read by `test_fits/bowl.py` (`CLEARANCE`) and `led_sun_lid/lid.py` (`SCREEN_CLEARANCE`). |
| `vessel_mouth_radial` | Slip into the vessel mouth | 0.0 | 2026-08-02 | A part seating in the mouth is cut *directly* to the 167mm top ID with nothing added. Confirmed by the LED Sun Lid prototype, which fitted perfectly at a 167.0 rim OD. |
| `ring_light_bore_radial` | Bore receiving the LED ring light | 0.0714 | 2026-08-02 | Not a chosen figure — it is what a round 89.5mm bore happens to leave over the ring's 89.3572mm OD, and it fitted perfectly, so it stands. See [led_ring_light.md](led_ring_light.md). |
| `passthrough_radial` | Cable and gland passthrough | 0.5 | — | Deliberately loose: the cut is a clearance route for something flexible being threaded through, not a fit. `led_sun_lid/lid.py`, `PASSTHROUGH_CLEARANCE`. |

## Notes

- Earlier cradle trials used **0.5mm radial**, which is why the first printed cradle engraved a bore of 181 for a 180 vessel. That figure is superseded; it is recorded here only so an old print's engraving can be explained.
- A fit only earns a Confirmed date by a part being printed and offered up to the real component. Until then it is a guess, however plausible — leave the Confirmed cell empty and say so.
- Two of these are *observed* rather than chosen: `vessel_mouth_radial` and `ring_light_bore_radial` are what a convenient round number left over the real component, kept because they worked. If either ever fails on a new part, the figure to revisit is the bore, not the component.
