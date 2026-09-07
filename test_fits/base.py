# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit solid for the vessel base (see ../spec/vessel.md).

A plain cylinder with its bottom edge filleted to CORNER_RADIUS, matching the
rounded corner where the vessel's side wall meets its base. Iterated against the
physical vessel until the cradle built from it fitted, which is what pinned the
base OD and corner radius down.

Both figures come from ../spec/vessel.md, not from literals here, because
test_fits/bowl.py cuts its cavity from this model and a number changed in one
place has to reach both. Change them in the document.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import specs
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

OD = specs.figure("vessel", "base_od")
CORNER_RADIUS = specs.figure("vessel", "base_corner_radius")
# Not a vessel figure -- just enough height to hold the corner radius and give
# something to grip while checking the fit, so it stays a literal.
HEIGHT = 20.0
# Measured 2026-08-09 and now a figure like any other. It was the tank's OD
# until then -- a stand-in so assembly.py could place the lid somewhere
# plausible -- and the guess was 1.4mm out, which is luck rather than method.
TANK_HEIGHT = specs.figure("vessel", "overall_height")

base = cq.Workplane("XY").circle(OD / 2).extrude(HEIGHT)
base = base.faces("<Z").edges().fillet(CORNER_RADIUS)
base = engrave_radial_text(base, f"{OD:.0f}", OD / 2, +1, HEIGHT / 2, theta0=0.0)

if __name__ == "__main__":
    show_object(base, name="test_fit_base")
    cq.exporters.export(base, str(OUTPUT_DIR / "base.step"))
