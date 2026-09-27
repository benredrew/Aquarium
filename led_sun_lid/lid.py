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
# Everything the lid has to fit around, read from the documents in ../spec/
# rather than restated here. The ring light's figures are supplied in imperial
# and converted once, in its own document.
VESSEL_TOP_ID = specs.figure("vessel", "top_opening_id")
LED_RING_OD = specs.figure("led_ring_light", "ring_od")
RING_LIGHT_THICKNESS = specs.figure("led_ring_light", "ring_thickness")
GLAND_DIA = specs.figure("led_ring_light", "gland_dia")
GLAND_PROTRUSION = specs.figure("led_ring_light", "gland_protrusion")
CABLE_DIA = specs.figure("led_ring_light", "cable_dia")

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
PASSTHROUGH_CLEARANCE = specs.figure("fits", "passthrough_radial")
PASSTHROUGH_BLEND = 0.5  # blend on the exterior edges the passthrough opens up
# Direction the cable leaves the hub, in degrees about Z. The cutters are built
# along +Y and rotated to suit, so 90 is the identity.
PASSTHROUGH_ANGLE = 90.0
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

# --- Screen interface ----------------------------------------------------
# The lid screen (../lid_screen/screen.py) drops into the open water between the
# hub and the rim and hangs on a lip let into the lid's top face. Both halves of
# that joint are dimensioned from here so they cannot drift apart: the lid cuts
# the rebate, the screen fills it.
#
# Clearance applies to the walls only. The z-normal faces are left tight, so the
# lip beds on the rebate floor and its top finishes flush with the lid face.
SCREEN_CLEARANCE = specs.figure("fits", "free_wall_radial")
SCREEN_LIP_WIDTH = 2.0  # reach of the lip past the screen wall, all the way round
SCREEN_LIP_DEPTH = 2.0  # rebate depth, and so the lip thickness
# Break on the lower edge of the rebate, where the floor meets the wall of the
# void proper -- the edge the screen's body passes as it drops through. Gives
# the screen a lead-in to meet the chamfer already on its own bottom edges.
# It is taken out of the floor, so it costs bearing: the lip lands on
# SCREEN_LIP_WIDTH minus SCREEN_CLEARANCE minus this.
SCREEN_REBATE_CHAMFER = 0.5

# Section height for sweep_prism. Anywhere in the full-width band between the
# bottom break and the top chamfer will do; mid-height is squarely inside it.
SECTION_SLAB = 0.02

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


def passthrough_cutters(angle_deg=None):
    """The solids the gland and cable sweep out on their way into the bore.

    The swept volume is the round gland plus everything directly above it: a
    cylinder that hugs the gland and cable, with a box standing on its axis to
    open the path up through the top face. The pocket keeps the round section
    so it follows the parts it clears.

    Built along +Y and then rotated to `angle_deg`, so the shape of the pocket
    is identical whichever way the cable faces.
    """
    if angle_deg is None:
        angle_deg = PASSTHROUGH_ANGLE
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

    delta = angle_deg - 90.0
    if abs(delta) > 1e-9:
        origin, z_axis = cq.Vector(0, 0, 0), cq.Vector(0, 0, 1)
        cutters = [c.rotate(origin, z_axis, delta) for c in cutters]
    return cutters


def blend_passthrough_edges(lid, angle_deg=None):
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


def cut_passthrough(lid, angle_deg=None):
    """Clear the ring light's cable gland and cable out through the hub wall.

    The light is installed by dropping it into the bore from above -- it cannot
    pass the retaining lip from below -- so what has to be removed is the
    *vertical sweep* of the gland and cable, not merely their final envelope.
    A pocket shaped to the envelope alone would trap the gland on the way in
    and leave the lid unassemblable, so everything from the gland axis upward
    is opened out through the top face.

    The gland sits at PASSTHROUGH_ANGLE, which must fall midway between two
    spokes so the cable exits into an open window rather than through structure.
    """
    # Cut one tool at a time. These four solids deliberately overlap each other,
    # and a Compound of overlapping solids is not a valid boolean argument --
    # OCC silently leaves material behind rather than erroring.
    for cutter in passthrough_cutters(angle_deg):
        lid = lid.cut(cq.Workplane(obj=cutter))
    return lid


# Angles (degrees) at which spokes are placed. The default is the full evenly
# spaced set; variants pass their own, see lid_two_spoke.py.
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
    lid = cut_passthrough(lid, passthrough_angle)
    lid = blend_passthrough_edges(lid, passthrough_angle)

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


def sweep_prism(lid_shape, section_z=None):
    """The volume `lid_shape` sweeps vertically, rather than the lid itself.

    Anything that has to drop into the lid from above has to clear where the lid
    is at every height on the way down, not only where it is at rest. Cutting a
    mating part against the lid solid lets it grow into the reliefs the top
    chamfer and bottom break open up, and those fillings then foul the
    full-width section the moment the part is lifted -- seated fine, impossible
    to install.

    One section through the full-width band, extruded through the travel, gives
    the silhouette that actually has to be cleared.
    """
    if section_z is None:
        section_z = THICKNESS / 2

    slab = (
        cq.Workplane("XY")
        .circle(OUTER_R + 5)
        .extrude(SECTION_SLAB)
        .translate((0, 0, section_z))
    )
    face = lid_shape.intersect(slab).faces(">Z").val()
    prism = cq.Solid.extrudeLinear(
        face.outerWire(), face.innerWires(), cq.Vector(0, 0, 3 * THICKNESS)
    )
    return cq.Workplane(obj=prism).translate((0, 0, -(THICKNESS + section_z)))


def section_outline(shape, z):
    """The outer boundary wire of `shape`'s horizontal section at height `z`."""
    slab = (
        cq.Workplane("XY")
        .circle(OUTER_R + 20)
        .extrude(SECTION_SLAB)
        .translate((0, 0, z - SECTION_SLAB))
    )
    return shape.intersect(slab).faces(">Z").val().outerWire()


def offset_solid(shape, distance):
    """`shape` grown by `distance` on every face.

    Run this on prisms -- the swept lid, the swept void -- not on the lid. A
    prism is planar ends and vertical walls, which the offset algorithm handles
    cleanly; the lid, with chamfers meeting fillets meeting the passthrough
    blend, is the kind of shape it returns a null result on.

    Growing a cutter is also the only way to get a gap that is uniform. Rotating
    a part slightly to open a gap at its ends only offsets a surface where that
    surface happens to run tangentially -- around a root fillet the normal
    points elsewhere and the gap collapses to a fraction of what was asked.
    """
    builder = BRepOffsetAPI_MakeOffsetShape()
    builder.PerformByJoin(
        shape.val().wrapped,
        distance,
        1e-6,
        BRepOffset_Mode.BRepOffset_Skin,
        False,
        False,
        GeomAbs_JoinType.GeomAbs_Arc,
        False,
    )
    builder.Build()
    return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))


lid = build_lid()

if __name__ == "__main__":
    show_object(lid, name="led_sun_lid")
    cq.exporters.export(lid, str(OUTPUT_DIR / "led_sun_lid.step"))
