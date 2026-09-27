# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""The Eclipse lid's screen -- the piece that fills its one large opening.

Same scheme as `lid_screen/screen.py`: a thin plate flush with the lid's top
face, carried on a rim that reaches down inside the opening, broken on the rim's
lower edge because that is the leading edge going in, and split into two solids
on the roof of the hollow so the plate can be run as bare infill while the rim
prints solid.

## Which opening

Eclipse has four. The hub bore holds the ring light and two strut bores are
holes through 6mm of wall; this fills the fourth, the large crescent left
between the mouth ring, the hub ring and the two struts. After the lid's own
+90 turn it faces -Y.

## How its outline is arrived at

Not from the four circles that bound the opening, which was the first attempt
and was wrong by 21 cubic millimetres. The lid's corners are blended to
MIN_Z_RADIUS, and a blend at a re-entrant corner *adds* material -- it fills the
notch where two circles cross, standing inside the opening where neither circle
says anything is. An outline drawn from the circles alone runs straight through
all ten of them.

So the outline comes from the lid itself: one section through its full-width
band, extruded through the travel, grown by the clearance. Sectioned rather than
cut against the lid solid because a mating part cut against the solid grows into
the reliefs the chamfers open up, and those fillings then foul the full-width
section the moment the part is lifted -- seated fine, impossible to install.
Grown rather than shrunk from a nominal, because growing the cutter is the only
way to get a gap that is the same everywhere.

Clearance goes on the walls and nowhere else: the plate finishes flush, so any
allowance in z would leave it standing proud or sunk.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import print_volume
import specs
from cadkit.viewer import show as show_object
from OCP.BRepOffset import BRepOffset_Mode
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
from OCP.GeomAbs import GeomAbs_JoinType

OUTPUT_DIR = Path(__file__).parent / "output"


def load_part(relative_path, name):
    """Import eclipse.py for its geometry only (no viewer, no export)."""
    path = Path(__file__).resolve().parent / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lid = load_part("eclipse.py", "eclipse")

SCREEN_THICKNESS = 4.0   # the plate, run as bare infill
RIM_HEIGHT = 8.0         # full height of the rim, down from the top face
RIM_THICKNESS = 2.0      # wall of the rim, all the way round
CHAMFER = 0.8            # break on the rim's lower edge, the leading edge in
# The top of the wall carries no break. It had a 1.0 chamfer briefly; removed
# on request. The top face is the one that finishes flush against nothing --
# it is the screen's own visible surface, not a mating face.

CLEARANCE = specs.figure("fits", "free_wall_radial")   # 0.2, walls only

# --- The lip ---------------------------------------------------------------
# Third feature, distinct from the screen and from the rim: the rim locates the
# screen in the opening, the lip stops it going through. It stands on the lid's
# top face and reaches outward over it, so all of it is added and none of it is
# taken out of the lid.
#
# Reach is bearing plus the lid's own top break. The first LIP_BEARING of any
# overhang lands on the chamfer, which is air -- reaching only the bearing would
# leave the lip resting on a 1mm sliver of the chamfer's outer lip instead of on
# the face.
LIP_HEIGHT = 2.0
LIP_BEARING = 2.0
LIP_REACH = LIP_BEARING + lid.TOP_BREAK      # 3.0

TOP_Z = lid.THICK                            # the lid's top face
RIM_BOTTOM_Z = TOP_Z - RIM_HEIGHT            # 8.0
PLATE_BOTTOM_Z = TOP_Z - SCREEN_THICKNESS    # 12.0 -- roof of the hollow
SCREEN_TOP_Z = TOP_Z + LIP_HEIGHT            # 18.0 -- the screen's own top

SCREEN_COLOR = (0, 0, 139)      # dark blue -- the solid rim
INFILL_COLOR = (120, 190, 235)  # pale blue -- the plate run as bare infill

SECTION_Z = lid.THICK / 2   # in the full-width band, clear of both edge breaks
SECTION_SLAB = 0.5


def prism():
    """The volume the lid sweeps vertically, rather than the lid itself."""
    slab = (
        cq.Workplane("XY")
        .workplane(offset=SECTION_Z)
        .circle(lid.OUTER_R + 5)
        .extrude(SECTION_SLAB)
    )
    face = lid.eclipse.intersect(slab).faces(">Z").val()
    return cq.Workplane(obj=cq.Solid.extrudeLinear(face, cq.Vector(0, 0, lid.THICK + 10))
                        ).translate((0, 0, -SECTION_Z - 5))


def offset_solid(shape, distance):
    """`shape` grown by `distance` on every face.

    Mirrors `led_sun_lid/lid.py`. Run on the prism, never on the lid: a prism is
    planar ends and vertical walls, which the offset algorithm handles cleanly,
    while the lid -- chamfers meeting blends meeting the passthrough -- is the
    kind of shape it hands back a null result on.
    """
    builder = BRepOffsetAPI_MakeOffsetShape()
    builder.PerformByJoin(
        shape.val().wrapped, distance, 1e-6,
        BRepOffset_Mode.BRepOffset_Skin, False, False,
        GeomAbs_JoinType.GeomAbs_Arc, False,
    )
    builder.Build()
    return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))


PRISM = prism()
GROWN = {}


def grown(distance):
    if distance not in GROWN:
        GROWN[distance] = offset_solid(PRISM, distance)
    return GROWN[distance]


def region(z0, z1):
    """The opening at height z0..z1, with the wall clearance already taken."""
    blank = (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .circle(lid.OUTER_R)
        .extrude(z1 - z0)
    )
    return largest(blank.cut(grown(CLEARANCE)))


def shrunk(z0, z1, inset, overshoot=1.0):
    """The same opening taken in by `inset`, by shrinking it rather than by
    growing the lid.

    Dilating the lid by clearance + rim thickness looked like the same thing and
    is not. The lid's members meet tangentially, so the opening pinches to a
    point at each meeting; grown by 2.2 the cutter closes those pinches, self-
    intersects, and the crescent disappears out of the result entirely. Shrinking
    the opening runs the offset inward instead, where a pinch simply retreats.

    Taken from the primitives, not by offsetting anything. Every offset route
    fails on this outline and for one reason: the lid's members meet
    tangentially, so the opening comes to a cusp at each meeting, and a cusp has
    no normal to offset along. BRepOffsetAPI garbles it at +2.2 and refuses it
    at -2.0; the 2D wire offset hands back a null shape.

    The four circles do not have that trouble. They are only approximate near
    the lid's ten blends -- a blend stands about 0.6mm into the opening and
    these circles do not know it -- but this outline sets the rim's *thickness*,
    not its fit. The outer face is the one that has to clear the lid, and that
    one still comes from the lid's own section. 2.0 of wall against a 0.6
    worst-case error keeps the rim on the right side of the opening throughout.
    """
    # `overshoot` runs the ends past z0 and z1. A cutter wants that; a piece of
    # the part does not, and the lip -- which is a piece of the part -- came out
    # 1mm long at the bottom and stood 1198 cubic millimetres inside the lid.
    body = (
        cq.Workplane("XY")
        .workplane(offset=z0 - overshoot)
        .circle(lid.OUTER_IR - CLEARANCE - inset)
        .extrude(z1 - z0 + 2 * overshoot)
    )
    blockers = [((lid.OFFSET, 0.0), lid.HUB_OR)] + [
        (centre, lid.STRUT_R) for centre in lid.STRUTS
    ]
    for (cx, cy), radius in blockers:
        body = body.cut(
            cq.Workplane("XY")
            .workplane(offset=z0 - overshoot - 1.0)
            .moveTo(cx, cy)
            .circle(radius + CLEARANCE + inset)
            .extrude(z1 - z0 + 2 * overshoot + 2.0)
        )
    # Built in the layout frame, where those constants live; the lid's own turn
    # has to be applied by hand here, unlike anything sectioned from the solid.
    return largest(body).rotate((0, 0, 0), (0, 0, 1), lid.PART_ROTATION)


def largest(body):
    """The biggest solid in `body`.

    Taking the opening out of a disc leaves slivers as well as the crescent --
    the strut bores, and whatever the clearance opens up where two circles were
    tangent. The crescent is the one this part is for, and it is larger than the
    rest by two orders of magnitude, so size picks it without a rule of thumb.
    """
    solids = body.val().Solids()
    if len(solids) <= 1:
        return body
    return cq.Workplane(obj=max(solids, key=lambda s: s.Volume()))


# The rim's inner face, over the screen's whole height. One region, used to
# hollow the skirt and to part the two bodies, so the wall cannot come out one
# thickness in the model and another in the split.
MIN_Z_RADIUS = lid.MIN_Z_RADIUS   # the lid's rule, applied to its screen
OUTER_RADIUS = MIN_Z_RADIUS + RIM_THICKNESS   # so the wall keeps its thickness
OUTER_SHARP = []                  # filled by build_screen
OUTER_USED = []

# --- The tips --------------------------------------------------------------
# The crescent ends in a taper at each strut. The lid's members are exactly
# tangent there, so after clearance the two boundaries cross at a hair under
# tangent -- 0.4mm of depth -- and the screen runs out to a knife edge.
#
# That edge cannot be filleted, at 4.5 or at 0.5, and for a while I read that as
# "these corners cannot be rounded". Wrong question. A tip with no included
# angle is not a corner to round, it is material that should not be there: trim
# it back to where the crescent has width and the trim leaves an ordinary corner
# that rounds like any other. Exactly what the profile gauge's base tongue
# needed, for exactly the same reason.
TIP_TRIM = 2.0

_TURN = math.radians(lid.PART_ROTATION)
STRUT_PLACED = [
    (x * math.cos(_TURN) - y * math.sin(_TURN),
     x * math.sin(_TURN) + y * math.cos(_TURN))
    for x, y in lid.STRUTS
]


def trim_tips(body):
    """Take the tapered ends off, back to where there is section to work with."""
    for cx, cy in STRUT_PLACED:
        body = body.cut(
            cq.Workplane("XY")
            .workplane(offset=RIM_BOTTOM_Z - 2.0)
            .moveTo(cx, cy)
            .circle(lid.STRUT_R + CLEARANCE + TIP_TRIM)
            .extrude(SCREEN_TOP_Z - RIM_BOTTOM_Z + 4.0)
        )
    return largest(body)


def build_screen():
    """Plate on a rim, both carried up past the lid's face into a lip."""
    # The outer face's radius is the inner face's plus the wall: that pair is
    # what keeps the rim one thickness the whole way round a corner.
    steps = (OUTER_RADIUS, 2.5, 2.0, 1.5, 1.0, 0.6)
    plate, s1, r1 = blend_stepped(region(PLATE_BOTTOM_Z, TOP_Z), steps)
    skirt_solid, s2, r2 = blend_stepped(region(RIM_BOTTOM_Z, PLATE_BOTTOM_Z), steps)
    OUTER_SHARP[:] = s1 + s2
    OUTER_USED[:] = [r1, r2]
    skirt = skirt_solid.cut(INNER)
    # Above the lid's face the whole section goes up together -- wall, field and
    # the outward flange -- so it is one plan, not three.
    whole = plate.union(skirt).union(LIP)

    # The wall is hollowed from radiused solids -- it is not radiused as a wall.
    #
    # That was the mistake behind a long run of refusals. A 2mm shell has its
    # other face 2mm away, so a 1.5 fillet on it breaks straight through and
    # OCC declines; every corner refused at every radius and it read like a
    # topology problem. It was not. Measured, twelve of these fourteen edges
    # meet at 60, 75, 113, 124, 126 and 138 degrees -- ordinary corners, and
    # they round without complaint on a solid prism. Only two are truly
    # tangent, and those two are the only ones that cannot.
    #
    # So the radii go on `plate`, `skirt` and `LIP` while each is still full
    # depth, and INNER carries its own; hollowing then leaves a wall that is
    # round on both faces and one thickness through the corner.
    wall, sharp = whole.cut(INNER), OUTER_SHARP + INNER_SHARP
    screen = whole

    # The break goes on the rim's underside only. Selecting by height rather
    # than by direction: the plate's own edges sit at TOP_Z and must stay
    # square, since that face finishes flush with the lid's.
    lower = [
        edge for edge in screen.val().Edges()
        if abs(edge.Center().z - RIM_BOTTOM_Z) < 1e-6
    ]
    # All together if OCC will take them, else one at a time. The opening's
    # boundary has cusps -- the lid's members meet each other tangentially by
    # design, so the crescent comes to a point at each of those meetings, and
    # the rim tapers to nothing there. A break needs an edge with two faces at
    # an angle; those have neither.
    skipped = sharp
    if lower:
        try:
            return screen.edges(_These(lower)).chamfer(CHAMFER), wall, skipped
        except Exception:
            pass
        good = []
        for edge in lower:
            try:
                screen.edges(_These([edge])).chamfer(CHAMFER)
                good.append(edge)
            except Exception:
                c = edge.Center()
                skipped.append((round(c.x, 1), round(c.y, 1)))
        # Each of `good` takes the break alone; together they can still refuse,
        # where two of them share a face and their breaks run into each other.
        # Step the size down rather than drop edges -- a uniform smaller break
        # reads as a decision, a missing one reads as a fault.
        for size in (CHAMFER, 0.6, 0.4, 0.3):
            try:
                screen = screen.edges(_These(good)).chamfer(size)
                break
            except Exception:
                continue
    return screen, wall, skipped


def corner_edges(shape):
    """The screen's vertical corners -- and not its cylinder seams.

    A closed cylindrical face carries a seam running parallel to Z that looks
    exactly like a corner to a direction filter, and rounding one cuts a groove
    down an otherwise smooth wall. The seam has the *same* face on both sides,
    though, while a corner has two different ones, so identity separates them
    with no tolerance to tune.

    Edges are taken from the solid, never from its faces. A face hands back its
    own copy of a shared edge, and the fillet builder will not accept one: it
    matches on the edge as it sits in the solid, so every Add made from a face's
    edge fails, at every radius, on corners that are plainly 60 or 120 degrees.
    That cost a long detour into imagined tangency problems.
    """
    solid = shape.val()
    faces = solid.Faces()
    keep = []
    for edge in shape.edges("|Z").vals():
        touching = [f for f in faces if any(e.wrapped.IsSame(edge.wrapped)
                                            for e in f.Edges())]
        if len(touching) == 2 and not touching[0].wrapped.IsSame(touching[1].wrapped):
            keep.append(edge)
    return keep


def blend_vertical(shape, radius):
    """Round every vertical corner to `radius`, reporting those that refuse.

    The opening's outline comes to a cusp wherever the lid's members meet
    tangentially, and a cusp has no included angle for a fillet to sit in. Those
    are named rather than allowed to fail the whole pass.
    """
    edges = corner_edges(shape)
    if not edges:
        return shape, []

    def blend(base, es):
        builder = BRepFilletAPI_MakeFillet(base.val().wrapped)
        for edge in es:
            builder.Add(radius, TopoDS.Edge_s(edge.wrapped))
        builder.Build()
        return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))

    try:
        return blend(shape, edges), []
    except Exception:
        pass
    good, skipped = [], []
    for edge in edges:
        try:
            blend(shape, [edge])
            good.append(edge)
        except Exception:
            c = edge.Center()
            skipped.append((round(c.x, 1), round(c.y, 1)))
    return (blend(shape, good) if good else shape), skipped


def blend_stepped(shape, radii):
    """Try each radius in turn; keep the first that rounds every corner."""
    out, sharp, used = shape, None, 0.0
    for radius in radii:
        blended, refused = blend_vertical(shape, radius)
        if sharp is None or len(refused) < len(sharp):
            out, sharp, used = blended, refused, radius
        if not refused:
            return blended, [], radius
    return out, sharp or [], used


class _These(cq.selectors.Selector):
    def __init__(self, edges):
        self.edges = edges

    def filter(self, objectList):
        return [
            o for o in objectList
            if any(o.wrapped.IsSame(e.wrapped) for e in self.edges)
        ]


def split_bodies(screen):
    """The wall, full height; and the field it encloses.

    Split on the rim's inner face rather than on a height. Parting it at the
    roof of the hollow cut the wall in two and handed its upper half to the
    infill body -- so the part that has to be solid, the rim, stopped being
    solid exactly where it becomes the lid's visible edge. The wall now runs
    z RIM_BOTTOM_Z to TOP_Z at full thickness whatever the plate does, and the
    infill body is only the field inside it.
    """
    # Parted on the radiused wall itself, not on INNER. The wall's corners were
    # rounded after INNER was made, so parting on INNER would hand the fillets
    # to the infill body and leave the wall square where it is meant to be
    # round -- the two would no longer be the two halves of what was built.
    return screen.intersect(WALL), screen.cut(WALL)


# No turn of its own. The outline is sectioned from `lid.eclipse`, which has
# already taken the lid's PART_ROTATION, so this is born in the placed frame --
# turning it again put it 90 degrees out and 7215 cubic millimetres inside the
# lid. Anything derived from the finished lid inherits its placement; only
# things built from the raw layout constants need turning.
# Blended before it is used, not after. This region is the rim's inner face and
# the surface the two bodies are parted on, so rounding it here is what makes
# the infill body come out matching the wall instead of squared off against a
# corner the wall no longer has.
INNER, INNER_SHARP, INNER_USED = blend_stepped(
    shrunk(RIM_BOTTOM_Z, SCREEN_TOP_Z, RIM_THICKNESS),
    (MIN_Z_RADIUS, 1.0, 0.6),
)

# The lip's outline is the same construction with the inset run the other way:
# a negative inset moves the mouth ring's circle outward and the hub's and
# struts' circles inward, which is exactly what overhanging the lid means.
#
# Its corners take MIN_Z_RADIUS + LIP_REACH, not MIN_Z_RADIUS. The lip's outer
# face is the rim's outer face pushed out by LIP_REACH, and a face offset by d
# takes its corner radius with it: a corner that is 1.5 on the rim is 1.5 + 3.0
# out here. Rounding it to 1.5 instead would make the lip pinch in at every
# corner rather than following the wall it overhangs.
#
# Blended on its own prism, before it is unioned into anything, for the same
# reason the wall is: plain cylinders meeting plain cylinders, with no step for
# the fillet to have to resolve against.
LIP_RADIUS = lid.MIN_Z_RADIUS + LIP_REACH
_LIP_PLAIN = shrunk(TOP_Z, SCREEN_TOP_Z, -LIP_REACH, overshoot=0.0)
LIP, LIP_SHARP, LIP_USED = _LIP_PLAIN, [], 0.0
for _r in (LIP_RADIUS, 3.5, 2.5, 1.5, 1.0, 0.5):
    _blended, _sharp = blend_vertical(_LIP_PLAIN, _r)
    if not _sharp:
        LIP, LIP_SHARP, LIP_USED = _blended, [], _r
        break
    LIP, LIP_SHARP, LIP_USED = _blended, _sharp, _r

screen, WALL, UNBROKEN = build_screen()
rim_body, plate_body = split_bodies(screen)

if __name__ == "__main__":
    show_object(lid.eclipse, name="eclipse_lid",
                options={"color": (250, 190, 60), "alpha": 1.0}, clear=True)
    show_object(rim_body, name="screen_rim",
                options={"color": SCREEN_COLOR, "alpha": 1.0})
    show_object(plate_body, name="screen_plate",
                options={"color": INFILL_COLOR, "alpha": 0.4})

    dx, dy, dz = print_volume.extents(screen)
    print(f"opening      mouth inner {lid.OUTER_IR:g}, hub outer {lid.HUB_OR:g}, "
          f"struts {lid.STRUT_R:.3f}, all at {CLEARANCE:g} wall clearance")
    print(f"plate        {SCREEN_THICKNESS:g} thick, z {PLATE_BOTTOM_Z:g} .. "
          f"{TOP_Z:g}, flush with the lid top")
    print(f"lip          {LIP_REACH:g} reach ({LIP_BEARING:g} bearing + "
          f"{lid.TOP_BREAK:g} over the lid's break), z {TOP_Z:g} .. "
          f"{SCREEN_TOP_Z:g}, sitting on the lid's face")
    print(f"rim          {RIM_THICKNESS:g} wall, z {RIM_BOTTOM_Z:g} .. "
          f"{SCREEN_TOP_Z:g}, {CHAMFER:g} break on its lower edge"
          + ", no break on its top"
          + (f"\n             LEFT SHARP: {len(UNBROKEN)} edges" if UNBROKEN else ""))
    print(f"lip corners  R{LIP_USED:g} used; R{LIP_RADIUS:g} asked for "
          f"({MIN_Z_RADIUS:g} global + {LIP_REACH:g} reach)"
          + (f" -- {len(LIP_SHARP)} still refused" if LIP_SHARP else " -- all took"))
    print(f"outer face   R{OUTER_USED[0]:g} plate / R{OUTER_USED[1]:g} skirt "
          f"(asked R{OUTER_RADIUS:g} = {MIN_Z_RADIUS:g} + {RIM_THICKNESS:g} wall)"
          + (f" -- {len(OUTER_SHARP)} refused" if OUTER_SHARP else " -- all took"))
    print(f"inner face   R{INNER_USED:g} (asked R{MIN_Z_RADIUS:g})"
          + (f" -- {len(INNER_SHARP)} refused" if INNER_SHARP else " -- all took"))
    print(f"extent       {dx:.2f} x {dy:.2f} x {dz:.2f} mm")
    print(f"bodies       rim {rim_body.val().Volume() / 1000:.1f} cm3, "
          f"plate {plate_body.val().Volume() / 1000:.1f} cm3, "
          f"{len(screen.val().Solids())} solid in the whole")

    # It has to go in. Anything shared with the lid is a place it will not.
    try:
        clash = screen.intersect(lid.eclipse)
        clash_vol = clash.val().Volume() if clash.val().Solids() else 0.0
    except ValueError:
        clash_vol = 0.0
    print(f"clash        {clash_vol:.6f} mm3 shared with the lid "
          f"({'clear' if clash_vol < 1e-6 else 'INTERFERES'})")
