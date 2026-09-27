# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Preview the whole stack: the cradle and vessel base at the bottom, the lid,
screen and ring light at the top.

Run this for the assembly view; run the individual part scripts for a single
part plus its STEP export. This script previews only -- it exports nothing,
since the assembly is not a printed thing.

The tank's height has never been measured. Everything above the base is placed
on the working assumption that the tank is as tall as it is wide, so the lid
sits TANK_HEIGHT above the vessel's bottom face. Treat the vertical gap as an
estimate; the parts themselves are all to size.
"""
import importlib.util
from pathlib import Path

from cadkit.viewer import show as show_object

ROOT = Path(__file__).parent

CRADLE_COLOR = (200, 200, 205)
BASE_COLOR = (140, 200, 255)
LID_COLOR = (255, 165, 0)
RING_COLOR = (0, 170, 70)
SCREEN_COLOR = (0, 0, 139)
INFILL_COLOR = (120, 190, 235)
ALPHA = 1.0  # solid


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


base_mod = load_part("test_fits/base.py", "base")
bowl_mod = load_part("test_fits/bowl.py", "bowl")
screen_mod = load_part("lid_screen/screen.py", "screen")
lid_variant = screen_mod.lid_variant  # already built, with its ring light

# The cradle has no floor, so the vessel drops until its corner radius meets the
# seat -- which puts its bottom face on z=0, the same plane the cradle sits on.
vessel_base = base_mod.base

# Lid, screen and light ride at the vessel mouth, TANK_HEIGHT above that face.
LID_Z = base_mod.TANK_HEIGHT


def at_mouth(part):
    return part.translate((0, 0, LID_Z))


show_object(
    bowl_mod.ring_clipped,
    name="cradle",
    options={"color": CRADLE_COLOR, "alpha": ALPHA},
    clear=True,
)
show_object(
    vessel_base, name="vessel_base", options={"color": BASE_COLOR, "alpha": ALPHA}
)
show_object(
    at_mouth(lid_variant.lid),
    name="led_sun_lid_two_spoke",
    options={"color": LID_COLOR, "alpha": ALPHA},
)
show_object(
    at_mouth(lid_variant.ring_light),
    name="led_ring_light",
    options={"color": RING_COLOR, "alpha": ALPHA},
)
show_object(
    at_mouth(screen_mod.solid_body),
    name="lid_screen_solid",
    options={"color": SCREEN_COLOR, "alpha": ALPHA},
)
show_object(
    at_mouth(screen_mod.infill_body),
    name="lid_screen_infill",
    options={"color": INFILL_COLOR, "alpha": ALPHA},
)

print(f"tank height assumed = OD = {base_mod.TANK_HEIGHT:g}mm (not measured)")
print(f"lid underside sits at z = {LID_Z:g}mm")
