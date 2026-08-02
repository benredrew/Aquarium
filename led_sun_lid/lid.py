# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""LED Sun Lid -- wheel-shaped lid that seats in the vessel mouth and carries
an LED ring light at its hub.

Geometry is a simple 2D profile extruded to THICKNESS: an outer rim sized to
the vessel top ID, a central hub bored to the LED ring OD, and spokes joining
the two. The only departure from the flat extrude is a lip at the bottom of
the hub bore that stops the ring light falling through.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
from cadquery.selectors import Selector
from engrave import engrave_radial_text
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepFilletAPI import BRepFilletAPI_MakeChamfer, BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Interface dimensions (measured) -------------------------------------
VESSEL_TOP_ID = 167.0  # see ../DIMENSIONS.md
LED_RING_OD_IN = 3.518
LED_RING_OD = LED_RING_OD_IN * 25.4  # 89.3572 mm
RING_LIGHT_THICKNESS = 0.525 * 25.4  # 13.3350 mm
GLAND_DIA = 0.34 * 25.4  # 8.6360 mm
GLAND_PROTRUSION = 0.07 * 25.4  # 1.7780 mm past the ring OD
CABLE_DIA = 0.125 * 25.4  # 3.1750 mm

# --- Design parameters ---------------------------------------------------
WALL = 6.0  # rim wall, hub wall and spoke width
CORNER_RADIUS = 6.0  # fillet on every vertical (Z-parallel) corner
CHAMFER = 1.0  # symmetric top break
# The bottom break is the overhanging one on an FDM printer, so it is cut
# shallower than the 45 degrees a symmetric chamfer would give. Measured from
# vertical: 45 is the usual printable limit, 30 leaves margin. Its two legs sum
# to BOTTOM_BREAK_SPAN, matching what the symmetric top break spends.
BOTTOM_BREAK_ANGLE = 30.0
BOTTOM_BREAK_SPAN = 2.0  # horizontal leg + vertical leg
# Extrude depth of the 2D profile. Set so the top chamfer starts clear of the
# passthrough pocket's tangent seam at GLAND_AXIS_Z: at 10.0 the chamfer began
# only 0.33mm above the seam, pinching out slivers too short to blend, which
# left the cable exit visibly sharp. At 10.5 the gap is 0.83mm and the edges
# there blend like any other.
THICKNESS = 10.5
SPOKE_COUNT = 6
LIP_WIDTH = 2.0  # radial reach of the retaining lip
LIP_HEIGHT = 2.0  # vertical thickness of the retaining lip
HUB_BORE = 89.5  # bore that hugs the ring light -- drives the fit
PASSTHROUGH_CLEARANCE = 0.5  # radial gap around the gland and cable
PASSTHROUGH_BLEND = 0.5  # blend on the exterior edges the passthrough opens up
# Edges shorter than this are not handed to the fillet builder directly; see
# blend_passthrough_edges. It wants to sit in the gap between the sliver edges
# the cut leaves behind (~0.33mm) and the real ones (>1.3mm).
BLEND_MIN_EDGE = 0.5

# --- Derived radii -------------------------------------------------------
SLIP_CLEARANCE = HUB_BORE - LED_RING_OD  # 0.1428 diametral, 0.0714 radial
OUTER_R = VESSEL_TOP_ID / 2  # 83.50
RIM_IR = OUTER_R - WALL  # 77.50
HUB_IR = HUB_BORE / 2  # 44.75 -- ring light drops in here
HUB_OR = HUB_IR + WALL  # 50.75
LIP_BORE_R = HUB_IR - LIP_WIDTH  # 42.75 -- ring light seats on this ledge

# The light rests on the lip, which fixes the height of its gland and cable.
GLAND_AXIS_Z = LIP_HEIGHT + RING_LIGHT_THICKNESS / 2  # 8.6675
GLAND_REACH = LED_RING_OD / 2 + GLAND_PROTRUSION  # 46.4566 from the axis

# Split the bottom break's span into its two legs. run/rise = tan(angle), and
# run + rise = span, so rise = span / (1 + tan(angle)).
BOTTOM_BREAK_RISE = BOTTOM_BREAK_SPAN / (
    1 + math.tan(math.radians(BOTTOM_BREAK_ANGLE))
)  # 1.2679
BOTTOM_BREAK_RUN = BOTTOM_BREAK_SPAN - BOTTOM_BREAK_RISE  # 0.7321

Y_AXIS = cq.Vector(0, 1, 0)

# Labels sit midway up, on the flat band of each interface surface: clear of
# the bottom break and the lip below, and of the top chamfer above.
LABEL_Z = THICKNESS / 2  # 5.25

# Spokes run past both junctions so the booleans fuse cleanly. Half a wall of
# overlap keeps the straight spoke ends buried in ring material without the
# rectangle's corners reaching the OD or intruding into the hub bore.
SPOKE_OVERLAP = WALL / 2
SPOKE_INNER_R = HUB_OR - SPOKE_OVERLAP
SPOKE_OUTER_R = RIM_IR + SPOKE_OVERLAP


class RadialBand(Selector):
    """Selects edges whose midpoint lies in an annular band about the Z axis.

    Used to isolate the spoke/ring junction corners at RIM_IR and HUB_OR from
    the seam edges that OCC leaves on the full cylinders at OUTER_R and HUB_IR,
    which are also Z-parallel but must not be filleted.
    """

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
    """Chamfer the bottom edges at BOTTOM_BREAK_ANGLE measured from vertical.

    Driven through OCC directly rather than Workplane.chamfer(run, rise),
    because that helper picks which of the edge's two faces receives which leg
    from internal face ordering. That ordering is not consistent edge to edge:
    it silently produced a mix of 30 and 60 degree breaks on this part. Naming
    the bottom face explicitly pins the run to the face and the rise to the
    wall for every edge.

    The lip is left sharp so its ledge keeps the full seating surface and
    cannot let the ring light creep past it. The lip's top edges sit at
    z=LIP_HEIGHT and so are not in this selection at all; its bottom edge
    shares the z=0 plane with the rest of the part and is excluded by radius.
    """
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
            # Dis1 is measured on the named face (the run across the bottom),
            # Dis2 on the wall (the rise).
            builder.Add(
                BOTTOM_BREAK_RUN,
                BOTTOM_BREAK_RISE,
                TopoDS.Edge_s(edge.wrapped),
                TopoDS.Face_s(face.wrapped),
            )

    builder.Build()
    return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))


def passthrough_cutters():
    """The solids the gland and cable sweep out on their way into the bore.

    The swept volume is the round gland plus everything directly above it: a
    cylinder that hugs the gland and cable, with a box standing on its axis to
    open the path up through the top face. The pocket keeps the round section
    so it follows the parts it clears.
    """
    gland_r = GLAND_DIA / 2 + PASSTHROUGH_CLEARANCE
    cable_r = CABLE_DIA / 2 + PASSTHROUGH_CLEARANCE
    y_start = HUB_IR - 5  # begin inside the bore, which is already void
    gland_end = GLAND_REACH + PASSTHROUGH_CLEARANCE
    cable_end = HUB_OR + 2  # fully clear of the hub's outer wall
    sweep_top = THICKNESS + 1  # break out through the top face

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
    return cutters


def blend_passthrough_edges(lid):
    """Blend the exterior edges the passthrough cut opened up.

    Two filters decide what qualifies.

    First, the edge has to have been *created* by the cut rather than merely
    trimmed by it. Edges like the hub bore's top edge survive the cut as
    shortened arcs and look new, but they are original edges that already carry
    their own chamfer and must not be blended again. A created edge lies on the
    cutting tool's surface; a trimmed one does not.

    Second, the blend has to remove material. A fillet on a convex edge cuts
    the corner away, but on a concave edge it fills the corner in, and the
    pocket around the gland has concave corners of its own. Convexity is judged
    by measuring the volume change of a trial fillet, which is decisive, rather
    than inferred from face orientation, which is not reliable to read off.
    Tangent edges -- where a sweep box meets the cylinder it was sized to match
    -- cannot be filleted at all, and drop out of the same trial.

    Edges shorter than BLEND_MIN_EDGE are withheld from the builder. The cut
    leaves a few 0.33mm slivers on the hub wall, where the tangent seam between
    the pocket's round section and its vertical sweep runs just below where the
    top chamfer begins. Handing those to the fillet builder alongside their
    neighbours segfaults OCC outright -- it takes the process down rather than
    raising, so it cannot be caught and retried. Withholding them costs
    nothing: blending the full-length edges around them consumes the slivers
    anyway, and re-running the search afterwards finds none left.
    """
    solid = lid.val()
    base_volume = solid.Volume()

    cutters = passthrough_cutters()
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
            continue  # trimmed by the cut, not created by it

        try:
            trial = _fillet(solid, [edge])
        except Exception:
            continue  # tangent or otherwise unfilletable
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


def cut_passthrough(lid):
    """Clear the ring light's cable gland and cable out through the hub wall.

    The light is installed by dropping it into the bore from above -- it cannot
    pass the retaining lip from below -- so what has to be removed is the
    *vertical sweep* of the gland and cable, not merely their final envelope.
    A pocket shaped to the envelope alone would trap the gland on the way in
    and leave the lid unassemblable, so everything from the gland axis upward
    is opened out through the top face.

    The gland sits at +Y, which falls midway between two spokes, so the cable
    exits into an open window rather than through structure.
    """
    # Cut one tool at a time. These four solids deliberately overlap each other,
    # and a Compound of overlapping solids is not a valid boolean argument --
    # OCC silently leaves material behind rather than erroring.
    for cutter in passthrough_cutters():
        lid = lid.cut(cq.Workplane(obj=cutter))
    return lid


def build_lid():
    rim = cq.Workplane("XY").circle(OUTER_R).circle(RIM_IR).extrude(THICKNESS)
    hub = cq.Workplane("XY").circle(HUB_OR).circle(HUB_IR).extrude(THICKNESS)

    lid = rim.union(hub)

    spoke_len = SPOKE_OUTER_R - SPOKE_INNER_R
    spoke_mid = (SPOKE_OUTER_R + SPOKE_INNER_R) / 2
    for i in range(SPOKE_COUNT):
        spoke = (
            cq.Workplane("XY")
            .rect(spoke_len, WALL)
            .extrude(THICKNESS)
            .translate((spoke_mid, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), 360.0 * i / SPOKE_COUNT)
        )
        lid = lid.union(spoke)

    # Round every vertical corner -- i.e. the spoke roots at both the rim and
    # the hub. Tolerance band excludes the cylinder seam edges at OUTER_R/HUB_IR.
    lid = (
        lid.edges("|Z")
        .edges(RadialBand(HUB_IR + 1e-6, OUTER_R - 1e-6))
        .fillet(CORNER_RADIUS)
    )

    # Retaining lip: a ledge around the bottom of the hub bore for the ring
    # light to sit on. Added after filleting so it does not perturb the
    # vertical-edge selection above.
    lip = (
        cq.Workplane("XY")
        .circle(HUB_IR)
        .circle(LIP_BORE_R)
        .extrude(LIP_HEIGHT)
    )
    lid = lid.union(lip)

    # Break the top and bottom edges. Done last so the lip is already present
    # and its edges can be excluded by the selector.
    # Top break is symmetric, so there is no face-ordering ambiguity to worry
    # about; the bottom one is angled and has to pin its faces explicitly.
    lid = lid.faces(">Z").edges().chamfer(CHAMFER)
    lid = break_bottom_edges(lid)

    # Cut last, so the passthrough's own edges are left sharp by the chamfer
    # selection above and get their own blend instead.
    lid = cut_passthrough(lid)
    lid = blend_passthrough_edges(lid)

    # Label the two interface diameters on the surfaces they actually control,
    # the same way the test rings are labelled: engraved, never raised. A boss
    # on the rim would fatten the OD that seats in the vessel, and one in the
    # bore would pinch the ring light. The bore label sits opposite the cable
    # passthrough so the two do not collide.
    lid = engrave_radial_text(
        lid, f"{VESSEL_TOP_ID:g}", OUTER_R, +1, LABEL_Z, theta0=0.0
    )
    lid = engrave_radial_text(
        lid, f"{HUB_BORE:g}", HUB_IR, -1, LABEL_Z, theta0=math.pi
    )
    return lid


lid = build_lid()

if __name__ == "__main__":
    show_object(lid, name="led_sun_lid")
    cq.exporters.export(lid, str(OUTPUT_DIR / "led_sun_lid.step"))
