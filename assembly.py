# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Preview the LED Sun Lid with the LED ring light seated in it.

Run this for the assembly view; run the individual part scripts for a single
part plus its STEP export. This script previews only -- it exports nothing,
since the assembly is not a printed thing.
"""
import importlib.util
from pathlib import Path

from ocp_vscode import show_object, set_port

set_port(3939)

ROOT = Path(__file__).parent

LID_COLOR = (255, 165, 0)
RING_COLOR = (0, 170, 70)
ALPHA = 0.5  # same on both so the two read alike where they overlap


def load_part(relative_path, name):
    """Import a part script for its geometry only.

    The part scripts guard their show/export behind __main__, so importing one
    here builds the model without pushing a second copy to the viewer or
    rewriting its STEP.
    """
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lid_mod = load_part("led_sun_lid/lid.py", "lid")
ring_mod = load_part("led_ring_light/ring_light.py", "ring_light")

# The light drops into the hub bore from above and rests on the retaining lip.
ring_light = ring_mod.ring_light.translate((0, 0, lid_mod.LIP_HEIGHT))

show_object(
    lid_mod.lid,
    name="led_sun_lid",
    options={"color": LID_COLOR, "alpha": ALPHA},
    clear=True,
)
show_object(
    ring_light,
    name="led_ring_light",
    options={"color": RING_COLOR, "alpha": ALPHA},
)
