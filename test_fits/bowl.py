# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit bowl -- the inverse of base.py: the cradle the vessel base sits in,
rather than a model of the vessel base itself.

The cradle is one sector of the same cavity profile base.py describes --
cylinder plus bottom corner radius -- grown by CLEARANCE. There is no floor:
the vessel is carried on the curved lip that reaches in under its corner
radius, so no material sits under the middle of the vessel where it would only
add mass.

The vessel is 180mm OD and the bed is 180mm square, so the full cradle ring
(188.2mm OD) does not fit. Two ways out are modelled here:

  `ring_clipped` -- the whole ring with everything outside the build volume
      trimmed off, leaving one connected body with four flats. This is what the
      module exports.
  `segments`     -- the ring cut into ARC_COUNT separate arcs, each printed on
      its own and assembled around the vessel. Kept because it is the stronger
      option; see the note on ring_clipped's webs below.

Reuses base.py's confirmed OD/height/corner-radius (rather than restating them)
so the two shapes cannot drift apart as either is refined.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import print_volume
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"


def load_part(relative_path, name):
    """Import base.py for its geometry/dimensions only (no viewer/export)."""
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_mod = load_part("base.py", "base")

# --- Print constraints ----------------------------------------------------
# Build volume lives in ../print_volume.py; see it in the preview.
EXTRUSION_WIDTH = 0.45  # 0.4mm nozzle, 0.20mm STRUCTURAL profile

# --- Design parameters ----------------------------------------------------
CLEARANCE = 0.5  # radial gap around the vessel base -- a cradle, not a slip fit
# Wall is a whole number of extrusion widths (8), so it prints as solid
# perimeters with no sliver of infill trapped in the middle.
WALL = 8 * EXTRUSION_WIDTH  # 3.60
# Tall enough to stand up past the corner radius onto the straight wall, which
# is what stops the vessel rocking; the grip itself is the lip below.
GRIP_HEIGHT = 12.0
ARC_COUNT = 4  # segments, for the `segments` alternative
ARC_ANGLE = 60.0  # degrees of vessel circumference each segment grips

CAVITY_R = base_mod.OD / 2 + CLEARANCE  # 90.50
CAVITY_CORNER_RADIUS = base_mod.CORNER_RADIUS + CLEARANCE  # 5.50
OUTER_R = CAVITY_R + WALL  # 94.10
# Innermost reach of the lip, where it tucks under the vessel's corner radius.
LIP_R = CAVITY_R - CAVITY_CORNER_RADIUS  # 85.00

# Label sits on the straight band of outer wall above the corner radius, and at
# 45 degrees -- on the diagonal, where the build volume clips nothing away. On
# axis the outer wall is trimmed off above the lip and the text would go with it.
LABEL_Z = (CAVITY_CORNER_RADIUS + GRIP_HEIGHT) / 2  # 8.75
LABEL_THETA = math.pi / 4


def sector(angle_deg, radius, height, rotation_deg):
    """A pie-slice solid, centred on `rotation_deg`, for trimming the ring.

    The outer arc is built through an explicit midpoint rather than with
    radiusArc: radiusArc's sign convention bowed the arc inward, toward the
    origin, which trimmed away the middle of every segment and left two thin
    slivers at the sector edges. threePointArc has no sign to get wrong.
    """
    half = math.radians(angle_deg / 2)
    start = (radius * math.cos(-half), radius * math.sin(-half))
    mid = (radius, 0.0)
    end = (radius * math.cos(half), radius * math.sin(half))
    return (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(*start)
        .threePointArc(mid, end)
        .close()
        .extrude(height)
        .rotate((0, 0, 0), (0, 0, 1), rotation_deg)
    )


def build_ring():
    """The full cradle ring, floorless -- 188.2mm OD, wider than the bed.

    Prints as-is with the z=0 face on the bed and needs no supports: the lip is
    the widest part and sits at the bottom, so every layer above is inset from
    the one below.
    """
    ring = cq.Workplane("XY").circle(OUTER_R).extrude(GRIP_HEIGHT)

    # The cavity runs the full height and out through the top -- no floor.
    cavity = cq.Workplane("XY").circle(CAVITY_R).extrude(GRIP_HEIGHT + 1)
    cavity = cavity.faces("<Z").edges().fillet(CAVITY_CORNER_RADIUS)
    ring = ring.cut(cavity)

    return engrave_radial_text(
        ring, f"{2 * CAVITY_R:g}", OUTER_R, +1, LABEL_Z, theta0=LABEL_THETA
    )


ring = build_ring()

# What survives inside the build volume: the ring with four flats milled off
# where it overran the bed, still one connected body.
ring_clipped = ring.intersect(print_volume.volume)

# The earlier alternative: four separate arcs, each well inside the bed.
segments = [
    ring.intersect(sector(ARC_ANGLE, OUTER_R + 5, GRIP_HEIGHT, 360.0 * i / ARC_COUNT))
    for i in range(ARC_COUNT)
]

if __name__ == "__main__":
    show_object(base_mod.base, name="vessel_base", clear=True)
    show_object(ring_clipped, name="bowl_ring_clipped")
    print_volume.show(show_object)

    dx, dy, dz = print_volume.extents(ring_clipped)
    print(f"clipped ring: {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(ring_clipped.val().Solids())} body, "
          f"{ring_clipped.val().Volume() / 1000:.1f} cm3")
    if print_volume.fits(ring_clipped):
        cq.exporters.export(ring_clipped, str(OUTPUT_DIR / "bowl_ring.step"))
    else:
        print(
            f"NOT exported: does not fit the "
            f"{print_volume.BED_X:g}x{print_volume.BED_Y:g}x{print_volume.BED_Z:g} "
            f"build volume."
        )
