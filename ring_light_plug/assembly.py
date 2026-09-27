"""Preview Vessel 2 with its Eclipse lid, LED ring, and plant-stem plug."""
import importlib.util
from pathlib import Path

from cadkit.viewer import show as show_object

ROOT = Path(__file__).resolve().parent.parent


def load(relative_path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lid = load("vessel_2_eclipse/eclipse.py", "vessel_2_eclipse_model")
light = load("led_ring_light_2/ring_light.py", "led_ring_light_2_model")
plant_lid = load("ring_light_plug/lid.py", "ring_light_plant_plug_model")
vessel = load("vessel_2_standin/standin.py", "vessel_2_standin_model")

# The lid's outward flange occupies its uppermost OD_LIP_THICKNESS. Its
# underside beds on the vessel rim; the rest of the mouth band hangs inside.
LID_Z = vessel.HEIGHT - (lid.THICK - lid.OD_LIP_THICKNESS)
eclipse = lid.display_eclipse.translate((0, 0, LID_Z))

# eclipse.display_eclipse restores the design frame for viewing. In that frame,
# the hub is OFFSET along +X and the ring's gland points through the -X cutout.
ring = light.ring_light.rotate(
    (0, 0, 0), (0, 0, 1), lid.PASSTHROUGH_ANGLE - 90.0
).translate((lid.OFFSET, 0, LID_Z + lid.LIP_HEIGHT))

# The body hangs inside the ring; the flange underside beds on its top face.
plug = plant_lid.plug.translate(
    (lid.OFFSET, 0, LID_Z + lid.RING_TOP_Z - plant_lid.BODY_HEIGHT)
)

if __name__ == "__main__":
    show_object(
        vessel.standin,
        name="vessel_2_standin",
        options={"color": (140, 200, 255), "alpha": 0.35},
    )
    show_object(
        eclipse,
        name="vessel_2_eclipse",
        options={"color": (250, 190, 60), "alpha": 1.0},
    )
    show_object(
        ring,
        name="led_ring_light_2",
        options={"color": (0, 170, 70), "alpha": 1.0},
    )
    show_object(
        plug,
        name="ring_light_plant_plug",
        options={"color": (80, 145, 210), "alpha": 1.0},
    )
