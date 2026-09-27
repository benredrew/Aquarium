<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Hacksaw — Specifications

A modern budget hacksaw taking a 12in / 300mm blade — the kind sold as a
hardware-store own brand with a tubular steel bow, a moulded pistol grip and a
tensioning knob or lever at the nose. The saw block is cut to guide *this*
blade, so every figure here is one the block's slot depends on.

Blades are consumables and vary between brands more than the frames do. These
are catalogue figures for a standard bi-metal blade, not measurements of the
blade in hand: **nothing here is confirmed by caliper yet.** Measure the blade
before trusting the slot width, and correct `blade_kerf` here rather than in
the model.

## Blade

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `blade_length` | Pin centre to pin centre | 12 in | 300.0 | The figure blades are sold by. Nominal — some brands cut it at 304.8mm (a true 12in) and rely on the tensioner to take up the difference. |
| `blade_depth` | Depth, tooth edge to back | 0.5 in | 12.7 | How much blade the guide slot has to work on at any instant. Sets the shortest bearing length the slot ever gets. |
| `blade_thickness` | Body thickness | 0.025 in | 0.63 | The steel itself, away from the teeth. |
| `blade_kerf` | Set width across the teeth | — | 0.90 | **The figure the slot is cut to, not `blade_thickness`.** The teeth are set wider than the body, so they, not the back, are what a slot has to pass. Typical for a 0.63mm bi-metal blade; measure yours. |

## Frame

| Key | Property | Imperial | Value (mm) | Notes |
|-----|----------|----------|------------|-------|
| `frame_depth` | Bow clearance below the blade | — | 100.0 | Blade line to the inside of the bow: the depth of cut the saw can reach before the frame fouls the work. Catalogue-typical for a 300mm frame; budget ones run 90–110mm. A junior hacksaw is nearer 60mm and will **not** clear the saw block's guide walls. |

## Notes

- Reference part: `saw_block/block.py`, which reads `blade_kerf` for its slot
  and checks its guide-wall height against `frame_depth`.
- **Unmeasured, and worth measuring:** how far the frame's blade-end fittings
  hang below the blade's tooth line. The saw block leaves 9mm between the
  blade at full depth and the bench; if the frame's ends drop more than that,
  they will touch the bench before the cut bottoms out. Nothing in the model
  reads this figure — it is a clearance to check on the real saw.
- Teeth point forward, so the cut is made on the push stroke, away from the
  user. That is the direction the saw block's bench-hook cleat resists.
