# Author: OpenAI Codex
# Co-Author: Brendan Fennell
"""Mock model of LED Ring Light 2 (see ../spec/led_ring_light_2.md)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import specs
from led_ring_light.ring_light import build_ring_light
from ocp_vscode import set_port, show_object

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

RING_OD = specs.figure("led_ring_light_2", "ring_od")
RING_ID = specs.figure("led_ring_light_2", "ring_id")
RING_THICKNESS = specs.figure("led_ring_light_2", "ring_thickness")
CABLE_DIA = specs.figure("led_ring_light_2", "cable_dia")
GLAND_DIA = specs.figure("led_ring_light_2", "gland_dia")
GLAND_PROTRUSION = specs.figure("led_ring_light_2", "gland_protrusion")
CABLE_PROTRUSION = specs.figure("led_ring_light_2", "cable_protrusion")

ring_light = build_ring_light(
    ring_od=RING_OD,
    ring_id=RING_ID,
    ring_thickness=RING_THICKNESS,
    cable_dia=CABLE_DIA,
    gland_dia=GLAND_DIA,
    gland_protrusion=GLAND_PROTRUSION,
    cable_protrusion=CABLE_PROTRUSION,
    label="2",
)

if __name__ == "__main__":
    show_object(ring_light, name="led_ring_light_2")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(ring_light, str(OUTPUT_DIR / "ring_light_2.step"))
