<!--
Author: Claude (Sonnet 5)
Co-Author: Brendan Fennell
-->
# LED Ring Light — Specifications

Confirmed specifications of the LED ring light carried by the LED Sun Lid. Only record values that have been measured or taken from the manufacturer — not trial values used in scripts.

Supplied in imperial. The **Value (mm)** column is the converted figure, and it is the one the models read — `specs.figure("led_ring_light", "ring_od")` — so the conversion is done once, here, rather than in each script. The Imperial column is kept as the provenance of each number, not as a second source to convert from.

## Ring

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `ring_od` | Outer diameter | 3.518 in | 89.3572 | Drives the hub bore of the LED Sun Lid. |
| `ring_id` | Inner diameter | 1.93 in | 49.0220 | |
| `ring_thickness` | Thickness | 0.525 in | 13.3350 | Along the ring's primary (Z) axis. |

## Cable Passthrough

The gland and cable are coaxial and protrude parallel to **+Y**, centred at the ring's mid-thickness, taking the ring's primary axis as **Z**.

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `cable_dia` | Cable diameter | 0.125 in | 3.1750 | |
| `gland_dia` | Gland diameter | 0.34 in | 8.6360 | Fits inside the 13.3350 ring thickness. |
| `gland_protrusion` | Gland protrusion | 0.07 in | 1.7780 | Reach beyond the ring OD at the tangent point. |
| `cable_protrusion` | Cable protrusion | — | 12.0 | Assumed, beyond the gland face. Not a manufacturer figure. |

Resulting envelope, measured from the ring axis along +Y:

- Ring OD tangent: **44.6786**
- Gland face: **46.4566**
- Cable tip: **58.4566**

## Electrical

| Property | Value | Notes |
|----------|-------|-------|
| Voltage  |       | |
| Current  |       | |
| Power    |       | |

## Notes

- OD is the reference dimension for the lid hub bore. The lid drives its bore from `HUB_BORE` (currently 89.5mm) and derives the clearance from it — **0.1428mm diametral / 0.0714mm radial** — rather than padding the value recorded here. Keep this table nominal.
- **Standard slip-fit bore: 89.5mm (0.1428mm diametral / 0.0714mm radial clearance over this OD).** Confirmed 2026-08-02 via the LED Sun Lid prototype (10.5mm-thickness revision, printed 2026-08-01) — fit perfectly. Use 89.5mm as the default bore diameter for any future part receiving this ring light.
- The lid's cable passthrough is cut at **+Y (90°)**, midway between two spokes, with `PASSTHROUGH_CLEARANCE` 0.5mm radial. Because the light is installed by dropping it into the bore from above, the cut is the *vertical sweep* of the gland and cable up through the top face, not just their seated envelope — an envelope-shaped pocket would trap the gland on the way in.
- Seating: the light rests on the lid's 2mm lip, putting its gland axis at z = 8.6675 in lid coordinates. Its 13.335 thickness then stands 4.835mm proud of the 10.5mm lid.
- The lid is 10.5mm rather than a round 10mm so its top chamfer clears the passthrough pocket's tangent seam at z = 8.6675. At 10mm the chamfer started 0.33mm above that seam and pinched out slivers too short to blend, leaving the cable exit sharp.
- Reference model: `led_ring_light/ring_light.py` — mock of the component, not a printed part.
- Related test fit: `test_fits/led_ring.py` (90mm bore, the first whole millimetre above the OD).
