# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Mock model of LED Ring Light 1 (see ../spec/led_ring_light.md).

This is a reference component, not a printed part -- it exists so the lid and
the test fits can be checked against the real envelope, including the cable
gland and cable that have to pass through the lid.

Axes: ring primary axis is Z, ring sits z=0..THICKNESS. The gland and cable are
coaxial and protrude along +Y at mid-thickness.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared specs

import cadquery as cq
import engrave
import specs
from cadquery.selectors import RadiusNthSelector
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Manufacturer dimensions ---------------------------------------------
# Supplied in imperial; ../spec/led_ring_light.md holds both the imperial
# figure and the millimetre conversion, and the conversion is done there once
# rather than here and again in the lid.
RING_OD = specs.figure("led_ring_light", "ring_od")
RING_ID = specs.figure("led_ring_light", "ring_id")
RING_THICKNESS = specs.figure("led_ring_light", "ring_thickness")
CABLE_DIA = specs.figure("led_ring_light", "cable_dia")
GLAND_DIA = specs.figure("led_ring_light", "gland_dia")
GLAND_PROTRUSION = specs.figure("led_ring_light", "gland_protrusion")
CABLE_PROTRUSION = specs.figure("led_ring_light", "cable_protrusion")

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

LABEL = "1"
LABEL_SIZE = 8.0
LABEL_DEPTH = 0.5
LABEL_OVERSHOOT = 0.1
# The resolved font, not a second reading of the environment. This line was
# `os.environ.get("AQUARIUM_FONT_PATH")`, which is None unless ./preview
# exported it -- so the label cutter below passed fontPath=None, CadQuery fell
# back to a font that does not exist here, and the part died in makeText with
# an IndexError naming neither fonts nor this variable. engrave.py resolves a
# font that is proven to render; there is no reason for a second copy of the
# lookup, and a second copy is exactly how this drifted.
FONT_PATH = engrave.FONT_PATH


def build_ring_light(
    ring_od=RING_OD,
    ring_id=RING_ID,
    ring_thickness=RING_THICKNESS,
    cable_dia=CABLE_DIA,
    gland_dia=GLAND_DIA,
    gland_protrusion=GLAND_PROTRUSION,
    cable_protrusion=CABLE_PROTRUSION,
    label=LABEL,
):
    mid_z = ring_thickness / 2
    gland_face_y = ring_od / 2 + gland_protrusion
    gland_start_y = ring_od / 2 - GLAND_EMBED
    cable_tip_y = gland_face_y + cable_protrusion
    recess_ir = ring_id / 2 + LAND_WIDTH
    recess_or = ring_od / 2 - LAND_WIDTH

    ring = (
        cq.Workplane("XY")
        .circle(ring_od / 2)
        .circle(ring_id / 2)
        .extrude(ring_thickness)
    )

    # Top face has exactly two circular edges; index 0 is the bore, 1 the rim.
    # Done before the gland is added so both edges are still full circles.
    ring = ring.faces(">Z").edges(RadiusNthSelector(0)).chamfer(TOP_BREAK)
    ring = ring.faces(">Z").edges(RadiusNthSelector(1)).fillet(TOP_BREAK)

    ring = ring.cut(
        cq.Workplane("XY")
        .circle(recess_or)
        .circle(recess_ir)
        .extrude(RECESS_DEPTH)
    )

    # A shallow numeral in the flat top annulus distinguishes the two sizes
    # in OCPViewer without changing any interface surface.
    label_radius = (ring_od + ring_id) / 4
    label_cutter = (
        cq.Workplane("XY")
        .workplane(offset=ring_thickness - LABEL_DEPTH)
        .center(-label_radius, 0)
        .text(
            label,
            LABEL_SIZE,
            LABEL_DEPTH + LABEL_OVERSHOOT,
            combine=False,
            kind="bold",
            fontPath=FONT_PATH,
        )
    )
    ring = ring.cut(label_cutter)

    gland = cq.Workplane(
        obj=cq.Solid.makeCylinder(
            gland_dia / 2,
            gland_face_y - gland_start_y,
            cq.Vector(0, gland_start_y, mid_z),
            Y_AXIS,
        )
    )

    # Cable starts back at the gland root so the two fuse into one solid; only
    # the CABLE_PROTRUSION beyond the gland face is actually visible.
    cable = cq.Workplane(
        obj=cq.Solid.makeCylinder(
            cable_dia / 2,
            cable_tip_y - gland_start_y,
            cq.Vector(0, gland_start_y, mid_z),
            Y_AXIS,
        )
    )

    return ring.union(gland).union(cable)


ring_light = build_ring_light()

if __name__ == "__main__":
    show_object(ring_light, name="led_ring_light_1")
    cq.exporters.export(ring_light, str(OUTPUT_DIR / "ring_light.step"))
