<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Lumber — Specifications

The sawn stock the saw block has to take. Unlike the other documents in this
folder, this one describes a *class* of component rather than one object: timber
is sold by nominal size and delivered smaller, rough, and rarely square.

That looseness is the reason the block registers the board against a single
wall rather than trapping it between two. A channel cut to hold the stock on
both faces would either refuse the wide end of the tolerance or let a narrow
board sit skewed; a board pressed against one reference wall is square whatever
its width.

## Design capacity

The largest section the block accepts. Anything smaller drops into the same
channel and rests on the same floor, so the cut stays square down to thin strip
wood — a 6mm board is guided exactly as a 45mm one is.

| Key | Stock | Nominal | Value (mm) | Notes |
|-----|-------|---------|------------|-------|
| `max_thickness` | Thickness, floor to top | — | 45.0 | Sets the guide wall height: the walls must stand clear above this for the blade to be guided from the first stroke. |
| `max_width` | Width, across the channel | — | 95.0 | Sets the channel width, and with it how far the blade has to reach. |

## Nominal 2x4

What a "2 by 4" actually measures once planed, for reference — the design
capacity above is deliberately larger so rough-sawn and damp stock still fits.

| Key | Stock | Nominal | Value (mm) | Notes |
|-----|-------|---------|------------|-------|
| `pse_2x4_thickness` | Planed 2x4 thickness | 2 in | 38.0 | 1.5in after planing. |
| `pse_2x4_width` | Planed 2x4 width | 4 in | 89.0 | 3.5in after planing. |

## Notes

- Reference part: `saw_block/block.py`.
- A hacksaw is not the right saw for 2x4 softwood — the fine teeth clog and the
  cut is slow. The capacity is here because the block was asked to take it;
  the block's own accuracy is unaffected either way.
