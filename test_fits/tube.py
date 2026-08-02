# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit ring for the vessel mouth (see ../DIMENSIONS.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from engrave import labelled_ring
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

OD = 167.0
WALL = 2.0
HEIGHT = 10.0
ID = OD - 2 * WALL

tube = labelled_ring(OD, WALL, HEIGHT)

show_object(tube, name="test_fit_tube")

cq.exporters.export(tube, str(OUTPUT_DIR / "tube.step"))
