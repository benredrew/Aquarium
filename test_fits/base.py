# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit solid for the vessel base (see ../DIMENSIONS.md).

A plain cylinder with its bottom edge filleted to CORNER_RADIUS, matching the
rounded corner where the vessel's side wall meets its base. Iterated against
the physical vessel to pin down the base OD and corner radius before the
support structure is designed around it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

OD = 180.0
HEIGHT = 20.0
CORNER_RADIUS = 5.0

base = cq.Workplane("XY").circle(OD / 2).extrude(HEIGHT)
base = base.faces("<Z").edges().fillet(CORNER_RADIUS)
base = engrave_radial_text(base, f"{OD:.0f}", OD / 2, +1, HEIGHT / 2, theta0=0.0)

if __name__ == "__main__":
    show_object(base, name="test_fit_base")
    cq.exporters.export(base, str(OUTPUT_DIR / "base.step"))
