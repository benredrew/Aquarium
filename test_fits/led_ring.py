# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit ring for the LED ring light (see ../spec/led_ring_light.md).

Bore is the first whole millimetre above the light's 89.3572mm OD, so this
checks how much clearance a nominal 90mm bore actually leaves once printed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from cadkit.engrave import labelled_ring
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

ID = 90.0  # first integer diameter above the LED ring light OD
WALL = 2.0
HEIGHT = 10.0
OD = ID + 2 * WALL

led_ring = labelled_ring(OD, WALL, HEIGHT)

show_object(led_ring, name="test_fit_led_ring")

cq.exporters.export(led_ring, str(OUTPUT_DIR / "led_ring.step"))
