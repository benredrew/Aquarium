# Author: OpenAI Codex
# Co-Author: Brendan Fennell
"""Plant-stem plug for the centre of LED Ring Light 2.

The cylindrical body drops into the light's centre bore and a flange at the
top stops it falling through. Three radial slots let plant stems enter from
the side before the plug is seated. The top and bottom rims of each slot are
filleted so the stems meet a rounded surface rather than a sharp printed edge.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
from cadkit.engrave import engrave_radial_text
import print_volume
import specs
from cadquery.selectors import Selector
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Interfaces ----------------------------------------------------------
RING_SPEC = "led_ring_light_2"
RING_ID = specs.figure(RING_SPEC, "ring_id")
RING_THICKNESS = specs.figure(RING_SPEC, "ring_thickness")

# --- Design parameters ---------------------------------------------------
BODY_OD = 50.0
RADIAL_CLEARANCE = (RING_ID - BODY_OD) / 2
BODY_HEIGHT = RING_THICKNESS
FLANGE_REACH = 4.0
FLANGE_OD = BODY_OD + 2 * FLANGE_REACH
FLANGE_HEIGHT = 2.0
TOTAL_HEIGHT = BODY_HEIGHT + FLANGE_HEIGHT

NOTCH_COUNT = 3
NOTCH_WIDTH = 5.0
NOTCH_BLEND = 1.0
ENTRANCE_BLEND = 1.0
LABEL_ANGLE = math.radians(60.0)  # halfway between the 0 and 120 degree slots

BODY_R = BODY_OD / 2
FLANGE_R = FLANGE_OD / 2
NOTCH_R = NOTCH_WIDTH / 2
# A seated stem touches the ring light bore at its radially outermost point.
NOTCH_END_R = RING_ID / 2 - NOTCH_R
# Depth is reported from the body OD to the deepest point of the rounded end.
NOTCH_DEPTH = BODY_R - (NOTCH_END_R - NOTCH_R)


class These(Selector):
    """Select an explicit, temporary set of topology edges."""

    def __init__(self, edges):
        self.edges = edges

    def filter(self, object_list):
        return [
            edge
            for edge in object_list
            if any(edge.wrapped.IsSame(target.wrapped) for target in self.edges)
        ]


def notch_cutter(angle):
    """One open radial slot with a semicircular, 5 mm inner end."""
    length = FLANGE_R - NOTCH_END_R + NOTCH_R + 2.0
    cutter = (
        cq.Workplane("XY")
        .center(NOTCH_END_R, 0)
        .circle(NOTCH_R)
        .extrude(TOTAL_HEIGHT)
        .union(
            cq.Workplane("XY")
            .center(NOTCH_END_R, -NOTCH_R)
            .rect(length, NOTCH_WIDTH, centered=(False, False))
            .extrude(TOTAL_HEIGHT)
        )
    )
    return cutter.rotate((0, 0, 0), (0, 0, 1), angle)


def edges_on_plane(shape, z):
    """Edges lying wholly in one horizontal end plane."""
    selected = []
    for edge in shape.val().Edges():
        vertices = edge.Vertices()
        if not vertices:
            continue
        zs = [vertex.Center().z for vertex in vertices]
        if all(abs(vertex_z - z) < 1e-6 for vertex_z in zs):
            selected.append(edge)
    return selected


def bottom_notch_edges(shape):
    """Bottom slot edges, excluding the cylindrical body rim."""
    selected = []
    inner_limit = BODY_R - 0.5
    for edge in edges_on_plane(shape, 0.0):
        vertices = edge.Vertices()
        radii = [math.hypot(vertex.Center().x, vertex.Center().y) for vertex in vertices]
        if min(radii) < inner_limit:
            selected.append(edge)
    return selected


def slot_entrance_edges(shape):
    """Vertical edges where slots break the body and flange cylinders."""
    selected = []
    for edge in shape.val().Edges():
        vertices = edge.Vertices()
        if edge.geomType() != "LINE" or len(vertices) != 2:
            continue
        a, b = (vertex.Center() for vertex in vertices)
        if math.hypot(a.x - b.x, a.y - b.y) > 1e-6:
            continue
        radius = math.hypot(a.x, a.y)
        if abs(radius - BODY_R) < 1e-5 or abs(radius - FLANGE_R) < 1e-5:
            selected.append(edge)
    return selected


def build():
    body = cq.Workplane("XY").circle(BODY_R).extrude(BODY_HEIGHT)
    flange = (
        cq.Workplane("XY")
        .workplane(offset=BODY_HEIGHT)
        .circle(FLANGE_R)
        .extrude(FLANGE_HEIGHT)
    )
    plug = body.union(flange)

    for index in range(NOTCH_COUNT):
        plug = plug.cut(notch_cutter(index * 360.0 / NOTCH_COUNT))

    entrance_edges = slot_entrance_edges(plug)
    if len(entrance_edges) != NOTCH_COUNT * 4:
        raise RuntimeError(
            f"expected {NOTCH_COUNT * 4} slot entrance edges, "
            f"found {len(entrance_edges)}"
        )
    plug = plug.edges(These(entrance_edges)).fillet(ENTRANCE_BLEND)

    # Round the entire exposed top perimeter: flange rim and all three slots.
    top_edges = edges_on_plane(plug, TOTAL_HEIGHT)
    plug = plug.edges(These(top_edges)).fillet(NOTCH_BLEND)

    # Keep the lower stem-contact edges rounded as in the first iteration.
    lower_edges = bottom_notch_edges(plug)
    plug = plug.edges(These(lower_edges)).fillet(NOTCH_BLEND)

    # Mark the main cylinder with the diameter it actually prints. Keep the
    # label recessed so it does not change the fit, and centre it in the clear
    # arc between two stem slots.
    plug = engrave_radial_text(
        plug,
        f"{BODY_OD:.1f}",
        BODY_R,
        +1,
        BODY_HEIGHT / 2,
        theta0=LABEL_ANGLE,
    )
    return plug


plug = build()
# Keep `plug` in its seated assembly frame. The exported/standalone part is
# inverted so the broad flange lies on the print bed without an overhang.
print_plug = (
    plug.rotate((0, 0, 0), (1, 0, 0), 180.0)
    .translate((0, 0, TOTAL_HEIGHT))
)

if __name__ == "__main__":
    show_object(
        print_plug,
        name="ring_light_plant_plug",
        options={"color": (80, 145, 210), "alpha": 1.0},
        clear=True,
    )
    dx, dy, dz = print_volume.extents(print_plug)
    print(f"body         {BODY_OD:.3f} dia x {BODY_HEIGHT:g} high")
    print(f"ring fit     {RADIAL_CLEARANCE:g} radial clearance in {RING_ID:.3f} bore")
    print(f"flange       {FLANGE_OD:.3f} dia x {FLANGE_HEIGHT:g} high")
    print(f"stem slots   {NOTCH_COUNT} x {NOTCH_WIDTH:g} wide, {NOTCH_DEPTH:.3f} deep")
    print(f"stem centres {NOTCH_END_R:.3f} from axis, tangent to {RING_ID:.3f} bore")
    print(f"slot blend   R{NOTCH_BLEND:g} top/bottom, R{ENTRANCE_BLEND:g} entrances")
    print("orientation  flange on print bed")
    print(f"extent       {dx:.2f} x {dy:.2f} x {dz:.2f} mm")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(print_plug, str(OUTPUT_DIR / "ring_light_plant_plug.step"))
