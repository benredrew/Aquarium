<!--
Author: OpenAI Codex
Co-Author: Brendan Fennell
-->
# LED Ring Light 2 — Specifications

The second size of LED ring light. Its ring OD is 0.5mm smaller than Ring
Light 1 and its ID is 1.5mm larger. All other dimensions are currently shared
with Ring Light 1 because no other differences have been reported.

## Ring

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `ring_od` | Outer diameter | — | 88.8572 | Ring Light 1 OD minus 0.5mm. |
| `ring_id` | Inner diameter | — | 50.5220 | Ring Light 1 ID plus 1.5mm. |
| `ring_thickness` | Thickness | 0.525 in | 13.3350 | Assumed unchanged from Ring Light 1. |

## Cable Passthrough

The gland and cable are coaxial and protrude parallel to **+Y**, centred at
the ring's mid-thickness, taking the ring's primary axis as **Z**.

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `cable_dia` | Cable diameter | 0.125 in | 3.1750 | Assumed unchanged from Ring Light 1. |
| `gland_dia` | Gland diameter | 0.34 in | 8.6360 | Assumed unchanged from Ring Light 1. |
| `gland_protrusion` | Gland protrusion | 0.07 in | 1.7780 | Assumed unchanged from Ring Light 1. |
| `cable_protrusion` | Cable protrusion | — | 12.0 | Assumed unchanged from Ring Light 1. |
| `cable_bend_od_od` | Min bend, outside to outside | 0.7 in | 17.7800 | Assumed unchanged from Ring Light 1. |

## Notes

- Reference model: `led_ring_light_2/ring_light.py`.
- The reference model is engraved **2** on top for visual identification.
- Using the proven 0.0714mm radial ring-light allowance gives this light an
  **89.0mm receiving bore**.
