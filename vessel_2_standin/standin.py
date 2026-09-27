# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""A printable standin for Vessel 2 -- a plain open-top cylinder to work

against while the glass itself is elsewhere, the way ../test_fits/base.py
stands in for Vessel 1's base. Vessel 2's own profile (see ../spec/vessel_2.md)
is still only one confirmed figure deep, so this does not attempt it -- it is
a shop-dimensioned tube, not a reading of the glass.

Only the ID comes from spec/: `top_opening_id`, the one row vessel_2.md has.
Everything else -- wall, bottom thickness, overall height -- is a dimension
Brendan gave directly for this standin, not a spec figure, so it stays a
literal here rather than a row in that document.

The dimensions were given in inches (shop units for this part); IN converts
each to mm once, at the top, rather than scattering `* 25.4` through the file.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared specs

import cadquery as cq
import specs
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

IN = 25.4  # mm per inch

ID = specs.figure("vessel_2", "top_opening_id")
WALL = 0.155 * IN
BOTTOM = 0.5 * IN
HEIGHT = 11.75 * IN
OD = ID + 2 * WALL

TOP_CHAMFER = 1.0

# Not a spec figure and not measured -- a modelling choice for a standin that
# only has to print clean and sit flat, the same status RIM_FILLET has in
# vessel/vessel.py. Well inside both the 12.7mm floor and the 3.94mm wall, so
# it cannot eat into either.
BOTTOM_FILLET = 3.0

body = cq.Workplane("XY").circle(OD / 2).extrude(HEIGHT)
body = body.faces("<Z").edges().fillet(BOTTOM_FILLET)  # outside, bottom corner

# Built as its own solid and filleted on its own bottom face, then subtracted --
# rounding the corner on a combined body would mean picking the one bottom-facing
# edge at z=BOTTOM out of several, where this needs no selector at all. Overshoots
# 1mm past the open top so the cut boolean has no coplanar top face to trip on
# (test_fits/bowl.py's build_ring does the same for its cavity).
cavity = cq.Workplane("XY").circle(ID / 2).extrude(HEIGHT - BOTTOM + 1)
cavity = cavity.faces("<Z").edges().fillet(BOTTOM_FILLET)  # inside, bottom corner
standin = body.cut(cavity.translate((0, 0, BOTTOM)))

# Open top: the remaining top face is an annulus, so this chamfers both its
# outer and inner rim in one pass.
standin = standin.faces(">Z").edges().chamfer(TOP_CHAMFER)

if __name__ == "__main__":
    show_object(standin, name="vessel_2_standin")
    print(f"ID     {ID:.2f} mm  (spec/vessel_2.md top_opening_id)")
    print(f"OD     {OD:.2f} mm")
    print(f"wall   {WALL:.3f} mm  (0.155in)")
    print(f"height {HEIGHT:.2f} mm  (11.75in)")
    print(f"bottom {BOTTOM:.2f} mm  (0.5in), fillet R{BOTTOM_FILLET:g} in/out")
    print(f"top chamfer {TOP_CHAMFER:g} mm, in/out")
    cq.exporters.export(standin, str(OUTPUT_DIR / "standin.step"))
    print("  wrote standin.step")
