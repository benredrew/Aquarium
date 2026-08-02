# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Mock model of the LED ring light itself (see ../LED_RING_LIGHT.md).

This is a reference component, not a printed part -- it exists so the lid and
the test fits can be checked against the real envelope, including the cable
gland and cable that have to pass through the lid.

Axes: ring primary axis is Z, ring sits z=0..THICKNESS. The gland and cable are
coaxial and protrude along +Y at mid-thickness.
"""
from pathlib import Path

import cadquery as cq
from cadquery.selectors import RadiusNthSelector
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

MM_PER_IN = 25.4

# --- Manufacturer dimensions (imperial as supplied) ----------------------
RING_OD = 3.518 * MM_PER_IN  # 89.3572
RING_ID = 1.93 * MM_PER_IN  # 49.0220
RING_THICKNESS = 0.525 * MM_PER_IN  # 13.3350
CABLE_DIA = 0.125 * MM_PER_IN  # 3.1750
GLAND_DIA = 0.34 * MM_PER_IN  # 8.6360
GLAND_PROTRUSION = 0.07 * MM_PER_IN  # 1.7780 -- reach beyond the OD tangent

CABLE_PROTRUSION = 12.0  # mm of cable beyond the gland face

# Top face edge treatment: 0.095 in = 2.413 mm, taken to the nearest whole
# millimetre. Chamfer on the bore, blend on the outside.
TOP_BREAK = 2.0

# Bottom face is split into three concentric rings: a 1mm land at the bore, a
# 1mm land at the rim, and the remainder between them recessed by RECESS_DEPTH
# so the light seats on the two lands only.
LAND_WIDTH = 1.0
RECESS_DEPTH = 1.0

# How far the gland boss is buried in the ring wall. Internal modelling detail
# only -- it never changes the external envelope, it just guarantees the boss
# fuses to the ring rather than sitting on it as a separate solid.
GLAND_EMBED = 2.0

# --- Derived -------------------------------------------------------------
MID_Z = RING_THICKNESS / 2
GLAND_FACE_Y = RING_OD / 2 + GLAND_PROTRUSION  # 46.4566
GLAND_START_Y = RING_OD / 2 - GLAND_EMBED
CABLE_TIP_Y = GLAND_FACE_Y + CABLE_PROTRUSION  # 58.4566

RECESS_IR = RING_ID / 2 + LAND_WIDTH  # 25.5110
RECESS_OR = RING_OD / 2 - LAND_WIDTH  # 43.6786

Y_AXIS = cq.Vector(0, 1, 0)


def build_ring_light():
    ring = (
        cq.Workplane("XY")
        .circle(RING_OD / 2)
        .circle(RING_ID / 2)
        .extrude(RING_THICKNESS)
    )

    # Top face has exactly two circular edges; index 0 is the bore, 1 the rim.
    # Done before the gland is added so both edges are still full circles.
    ring = ring.faces(">Z").edges(RadiusNthSelector(0)).chamfer(TOP_BREAK)
    ring = ring.faces(">Z").edges(RadiusNthSelector(1)).fillet(TOP_BREAK)

    ring = ring.cut(
        cq.Workplane("XY")
        .circle(RECESS_OR)
        .circle(RECESS_IR)
        .extrude(RECESS_DEPTH)
    )

    gland = cq.Workplane(
        obj=cq.Solid.makeCylinder(
            GLAND_DIA / 2,
            GLAND_FACE_Y - GLAND_START_Y,
            cq.Vector(0, GLAND_START_Y, MID_Z),
            Y_AXIS,
        )
    )

    # Cable starts back at the gland root so the two fuse into one solid; only
    # the CABLE_PROTRUSION beyond the gland face is actually visible.
    cable = cq.Workplane(
        obj=cq.Solid.makeCylinder(
            CABLE_DIA / 2,
            CABLE_TIP_Y - GLAND_START_Y,
            cq.Vector(0, GLAND_START_Y, MID_Z),
            Y_AXIS,
        )
    )

    return ring.union(gland).union(cable)


ring_light = build_ring_light()

if __name__ == "__main__":
    show_object(ring_light, name="led_ring_light")
    cq.exporters.export(ring_light, str(OUTPUT_DIR / "ring_light.step"))
