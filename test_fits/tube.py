# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit ring for a vessel mouth.

Shared between vessels: whichever one is currently being dialled in, drop its
caliper estimate or previous trial into OD below, print, and note the result
in PRINT_LOG.md under that vessel's own table. Nothing here reads spec/ by
key, on purpose -- a trial value is exactly what does *not* belong in a
confirmed document yet.

Currently probing Vessel 2's top opening (see ../spec/vessel_2.md). First
trial at 116 (the rounded-down caliper reading) printed loose, so this is
walking up from there -- currently 118.

A stop lip sits at the bottom, wider than OD, so the tube cannot slide all
the way through the mouth -- it seats depth-controlled against the rim
instead, the same LIP_WIDTH/LIP_HEIGHT naming led_sun_lid/lid.py and
eclipse_lid/eclipse.py use for their own retaining lips. The plain tube
above it is unchanged and still carries the OD/ID labels.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from engrave import labelled_ring
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

OD = 118.0
WALL = 2.0
ID = OD - 2 * WALL

LIP_WIDTH = 4.0    # 0.16in = 4.064mm, rounded down -- radial reach past OD
LIP_HEIGHT = 1.0   # vertical thickness of the lip

OVERALL_HEIGHT = 8.0              # tube + lip, the whole printed part
HEIGHT = OVERALL_HEIGHT - LIP_HEIGHT  # the plain tube's own height, above the lip

lip = (
    cq.Workplane("XY")
    .circle(OD / 2 + LIP_WIDTH)
    .circle(ID / 2)
    .extrude(LIP_HEIGHT)
)
tube = labelled_ring(OD, WALL, HEIGHT).translate((0, 0, LIP_HEIGHT)).union(lip)

show_object(tube, name="test_fit_tube")

cq.exporters.export(tube, str(OUTPUT_DIR / "tube.step"))
