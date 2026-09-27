# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit ring for a vessel mouth.

Shared between vessels: whichever one is currently being dialled in, drop its
caliper estimate or previous trial into OD below, print, and note the result
in PRINT_LOG.md under that vessel's own table. Nothing here reads spec/ by
key, on purpose -- a trial value is exactly what does *not* belong in a
confirmed document yet.

Currently probing a 62mm candidate OD for the LED Ring Light 2 centre bore.
This is a trial value only; it does not belong in spec/ until a printed fit
confirms it.

This trial is a plain tube without a stop lip. It carries engraved OD/ID
labels on its cylindrical surfaces.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from engrave import labelled_ring
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

parser = argparse.ArgumentParser(description="Export a labelled cylindrical tube test fit.")
parser.add_argument("--od", type=float, default=62.0, help="outer diameter in mm (default: 62)")
args = parser.parse_args()

OD = args.od
WALL = 2.0
ID = OD - 2 * WALL

HEIGHT = 8.0

tube = labelled_ring(OD, WALL, HEIGHT)

show_object(
    tube,
    name="test_fit_tube",
    clear=True,
    reset_camera="reset",
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
cq.exporters.export(tube, str(OUTPUT_DIR / "tube.step"))
