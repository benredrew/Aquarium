# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Vessel 2 Lid -- wheel-shaped lid, same design language as the LED Sun Lid
(../led_sun_lid/lid.py), carrying LED Ring Light 2 at its hub and cut to
Vessel 2's 118mm mouth instead of Vessel 1's 167mm.

At this vessel's opening, the ring light leaves far less room to spare: only
14.5mm radial between the hub bore and the vessel wall, against 33mm on
Vessel 1. Kept the Sun Lid's 6mm rim and hub walls anyway (Brendan's call,
2026-09-01) rather than thinning them to make room -- that leaves only 2.5mm
of open annulus for the spokes to cross, so the lattice between hub and rim
reads as narrow slits rather than open water. It is a near-solid disc with a
ring-light hub, not a scaled-down Sun Lid in proportion.

Geometry pipeline mirrors lid.py exactly: 2D profile extruded to THICKNESS,
outer rim to the vessel mouth, central hub bored to the ring light, spokes
between, a lip to stop the ring falling through, top/bottom breaks, and a
passthrough pocket for the gland and cable. Duplicated rather than imported
because the two lids no longer share an interface diameter to hold constant
across -- see led_sun_lid/lid_two_spoke.py for the pattern used when they do.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import specs
from cadquery.selectors import Selector
from engrave import engrave_radial_text
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet
from OCP.BRepOffset import BRepOffset_Mode
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
from OCP.GeomAbs import GeomAbs_JoinType
from OCP.TopoDS import TopoDS
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Interface dimensions ------------------------------------------------
VESSEL_TOP_ID = specs.figure("vessel_2", "top_opening_id")
RING_SPEC = "led_ring_light_2"
LED_RING_OD = specs.figure(RING_SPEC, "ring_od")
RING_LIGHT_THICKNESS = specs.figure(RING_SPEC, "ring_thickness")
GLAND_DIA = specs.figure(RING_SPEC, "gland_dia")
GLAND_PROTRUSION = specs.figure(RING_SPEC, "gland_protrusion")
CABLE_DIA = specs.figure(RING_SPEC, "cable_dia")

# --- Design parameters ---------------------------------------------------
# Same as led_sun_lid/lid.py -- kept equal on purpose, see module docstring.
WALL = 6.0
CORNER_RADIUS = 1.0
CHAMFER = 1.0
BOTTOM_BREAK_ANGLE = 30.0
BOTTOM_BREAK_SPAN = 2.0
THICKNESS = 10.5
SPOKE_COUNT = 6
LIP_WIDTH = 2.0
LIP_HEIGHT = 2.0
HUB_BORE = LED_RING_OD + 2 * specs.figure("fits", "ring_light_bore_radial")
PASSTHROUGH_CLEARANCE = specs.figure("fits", "passthrough_radial")
PASSTHROUGH_BLEND = 0.5
PASSTHROUGH_ANGLE = 90.0
BLEND_MIN_EDGE = 0.5

# --- Derived radii -------------------------------------------------------
SLIP_CLEARANCE = HUB_BORE - LED_RING_OD  # 0.1428 diametral, 0.0714 radial
OUTER_R = VESSEL_TOP_ID / 2  # 59.00
RIM_IR = OUTER_R - WALL  # 53.00
HUB_IR = HUB_BORE / 2  # 44.50 -- Ring Light 2 drops in here
HUB_OR = HUB_IR + WALL  # 50.50
LIP_BORE_R = HUB_IR - LIP_WIDTH  # 42.50 -- ring light seats on this ledge

# RIM_IR - HUB_OR = 2.50mm: the entire radial budget spokes have to cross,
# see module docstring. On the Sun Lid this gap is 26.75mm.

GLAND_AXIS_Z = LIP_HEIGHT + RING_LIGHT_THICKNESS / 2  # 8.6675, unchanged from the Sun Lid
GLAND_REACH = LED_RING_OD / 2 + GLAND_PROTRUSION  # 46.4566 from the axis

BOTTOM_BREAK_RISE = BOTTOM_BREAK_SPAN / (
    1 + math.tan(math.radians(BOTTOM_BREAK_ANGLE))
)  # 1.2679
BOTTOM_BREAK_RUN = BOTTOM_BREAK_SPAN - BOTTOM_BREAK_RISE  # 0.7321

Y_AXIS = cq.Vector(0, 1, 0)

SECTION_SLAB = 0.02
LABEL_Z = THICKNESS / 2

SPOKE_OVERLAP = WALL / 2
SPOKE_INNER_R = HUB_OR - SPOKE_OVERLAP
SPOKE_OUTER_R = RIM_IR + SPOKE_OVERLAP


class RadialBand(Selector):
    """Selects edges whose midpoint lies in an annular band about the Z axis."""

    def __init__(self, r_min, r_max):
        self.r_min = r_min
        self.r_max = r_max

    def filter(self, objectList):
        keep = []
        for obj in objectList:
            c = obj.Center()
            r = math.hypot(c.x, c.y)
            if self.r_min < r < self.r_max:
                keep.append(obj)
        return keep


def break_bottom_edges(lid):
    """Chamfer the bottom edges at BOTTOM_BREAK_ANGLE measured from vertical."""
    solid = lid.val()
    builder = BRepFilletAPI_MakeChamfer(solid.wrapped)

    for face in solid.Faces():
        if abs(face.Center().z) > 1e-6:
            continue
        for edge in face.Edges():
            if all(
                abs(math.hypot(v.X, v.Y) - LIP_BORE_R) < 1e-6
                for v in edge.Vertices()
            ):
                continue  # bottom of the lip
            builder.Add(
                BOTTOM_BREAK_RUN,
                BOTTOM_BREAK_RISE,
                TopoDS.Edge_s(edge.wrapped),
                TopoDS.Face_s(face.wrapped),
            )

    builder.Build()
    return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))


def passthrough_cutters(angle_deg=None):
    """The solids the gland and cable sweep out on their way into the bore."""
    if angle_deg is None:
        angle_deg = PASSTHROUGH_ANGLE
    gland_r = GLAND_DIA / 2 + PASSTHROUGH_CLEARANCE
    cable_r = CABLE_DIA / 2 + PASSTHROUGH_CLEARANCE
    y_start = HUB_IR - 5
    gland_end = GLAND_REACH + PASSTHROUGH_CLEARANCE
    cable_end = HUB_OR + 2
    sweep_top = THICKNESS + 1

    cutters = []
    for radius, y_end in ((gland_r, gland_end), (cable_r, cable_end)):
        cutters.append(
            cq.Solid.makeCylinder(
                radius, y_end - y_start, cq.Vector(0, y_start, GLAND_AXIS_Z), Y_AXIS
            )
        )
        cutters.append(
            cq.Solid.makeBox(
                2 * radius,
                y_end - y_start,
                sweep_top - GLAND_AXIS_Z,
                cq.Vector(-radius, y_start, GLAND_AXIS_Z),
            )
        )

    delta = angle_deg - 90.0
    if abs(delta) > 1e-9:
        origin, z_axis = cq.Vector(0, 0, 0), cq.Vector(0, 0, 1)
        cutters = [c.rotate(origin, z_axis, delta) for c in cutters]
    return cutters


def blend_passthrough_edges(lid, angle_deg=None):
    """Blend the exterior edges the passthrough cut opened up."""
    solid = lid.val()
    base_volume = solid.Volume()

    cutters = passthrough_cutters(angle_deg)
    tool = cutters[0]
    for extra in cutters[1:]:
        tool = tool.fuse(extra)

    keep = []
    for edge in solid.Edges():
        if edge.Length() < BLEND_MIN_EDGE:
            continue
        point = edge.positionAt(0.5)
        probe = BRepExtrema_DistShapeShape(
            BRepBuilderAPI_MakeVertex(point.toPnt()).Vertex(), tool.wrapped
        )
        probe.Perform()
        if probe.Value() > 1e-6:
            continue

        try:
            trial = _fillet(solid, [edge])
        except Exception:
            continue
        if trial.Volume() < base_volume:
            keep.append(edge)

    if not keep:
        return lid
    return cq.Workplane(obj=_fillet(solid, keep))


def _fillet(solid, edges):
    builder = BRepFilletAPI_MakeFillet(solid.wrapped)
    for edge in edges:
        builder.Add(PASSTHROUGH_BLEND, TopoDS.Edge_s(edge.wrapped))
    builder.Build()
    return cq.Shape.cast(builder.Shape())


def cut_passthrough(lid, angle_deg=None):
    for cutter in passthrough_cutters(angle_deg):
        lid = lid.cut(cq.Workplane(obj=cutter))
    return lid


SPOKE_ANGLES = [360.0 * i / SPOKE_COUNT for i in range(SPOKE_COUNT)]


def build_lid(spoke_angles=None, passthrough_angle=None):
    if spoke_angles is None:
        spoke_angles = SPOKE_ANGLES
    if passthrough_angle is None:
        passthrough_angle = PASSTHROUGH_ANGLE

    rim = cq.Workplane("XY").circle(OUTER_R).circle(RIM_IR).extrude(THICKNESS)
    hub = cq.Workplane("XY").circle(HUB_OR).circle(HUB_IR).extrude(THICKNESS)

    lid = rim.union(hub)

    spoke_len = SPOKE_OUTER_R - SPOKE_INNER_R
    spoke_mid = (SPOKE_OUTER_R + SPOKE_INNER_R) / 2
    for angle in spoke_angles:
        spoke = (
            cq.Workplane("XY")
            .rect(spoke_len, WALL)
            .extrude(THICKNESS)
            .translate((spoke_mid, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        lid = lid.union(spoke)

    lid = (
        lid.edges("|Z")
        .edges(RadialBand(HUB_IR + 1e-6, OUTER_R - 1e-6))
        .fillet(CORNER_RADIUS)
    )

    lip = (
        cq.Workplane("XY")
        .circle(HUB_IR)
        .circle(LIP_BORE_R)
        .extrude(LIP_HEIGHT)
    )
    lid = lid.union(lip)

    lid = lid.faces(">Z").edges().chamfer(CHAMFER)
    lid = break_bottom_edges(lid)

    lid = cut_passthrough(lid, passthrough_angle)
    lid = blend_passthrough_edges(lid, passthrough_angle)

    lid = engrave_radial_text(
        lid, f"{VESSEL_TOP_ID:g}", OUTER_R, +1, LABEL_Z, theta0=0.0
    )
    lid = engrave_radial_text(
        lid, f"{HUB_BORE:g}", HUB_IR, -1, LABEL_Z, theta0=math.pi
    )
    return lid


lid = build_lid()

if __name__ == "__main__":
    show_object(lid, name="vessel_2_lid")
    cq.exporters.export(lid, str(OUTPUT_DIR / "vessel_2_lid.step"))
