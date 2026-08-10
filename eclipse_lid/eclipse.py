# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Eclipse -- a lid made of two rings of mass, tangent at one point.

Two bands, each BRANCH wide. One sized to the vessel's mouth, one to the ring
light. Their *centrelines* are placed tangent, which offsets the light from the
tank's axis and is where the name comes from.

## Why the tangency does more than it looks like

Both bands are the same width, so putting the centrelines tangent puts every
boundary tangent: the outer circles touch at one point, and so do the inner
ones. The union has no crossing corner anywhere near the join -- the two rings
run into each other smoothly, and the only corners in the whole plan are the two
places the small ring's outer circle cuts the large ring's inner one, well away
on either side.

Equal widths are what buys that. Give the two bands different widths and the
tangency of the centrelines buys nothing: all four boundaries cross, and the
join grows four corners instead of none.

## What drives what

Nothing here is a chosen diameter. The outer band is the vessel's top opening
(spec/vessel.md, seated with no allowance at all per spec/fits.md) and the inner
band is the standard 89.5 slip bore over the ring light's OD. The offset falls
out of those two and BRANCH; it is not a placement.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import print_volume
import specs
from ocp_vscode import show_object, set_port
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

PART_ROTATION = 90.0    # about +Z, right hand, applied to the finished body
THICK = 16.0            # z
BRANCH = 6.0            # radial width of both bands
MIN_Z_RADIUS = 1.5      # least radius allowed about a vertical axis

# --- The two bands ---------------------------------------------------------
# A part seating in the mouth is cut directly to the top ID: vessel_mouth_radial
# is 0.0, and that is a confirmed observation, not an oversight.
MOUTH_ID = specs.figure("vessel", "top_opening_id")
MOUTH_FIT = specs.figure("fits", "vessel_mouth_radial")
HUB_BORE = 89.5         # the standard slip bore over the ring light's OD
RING_OD = specs.figure("led_ring_light", "ring_od")
RING_THICK = specs.figure("led_ring_light", "ring_thickness")

OUTER_R = MOUTH_ID / 2 - MOUTH_FIT      # 83.5
OUTER_IR = OUTER_R - BRANCH             # 71.5
HUB_IR = HUB_BORE / 2                   # 44.75
HUB_OR = HUB_IR + BRANCH                # 56.75

# Centrelines, and the offset that makes them touch.
OUTER_CL = (OUTER_R + OUTER_IR) / 2     # 77.5
HUB_CL = (HUB_IR + HUB_OR) / 2          # 50.75
OFFSET = OUTER_CL - HUB_CL              # 26.75, along +X

# --- The two struts --------------------------------------------------------
# C and D. Plain cylinders, each tangent to A and to B, off the x-axis and not
# on each other -- which leaves exactly one pair, mirrored about y=0.
#
# Tangent to the two *centrelines*, the same way A and B were placed against
# each other. Tangency to the ring surfaces instead would put each strut against
# a ring at a single point, and a union joined through a point is not a solid.
# On the centrelines each strut overlaps its ring by
# (BRANCH/2 + STRUT_R) - STRUT_R = BRANCH/2, so there is real material at both
# ends of it.
# Tangency is centreline to centreline, as it is between A and B -- the strut's
# own centreline circle touching theirs, not its outer face touching theirs.
# The face reading put the whole strut a half-wall too far in and made it a
# different kind of joint from the one holding A to B.
#
# The radius is not chosen either: it is whatever puts the centres on the gland
# exit axis, x = OFFSET. With a = OUTER_CL, b = HUB_CL, o = OFFSET (= a - b) and
# c the strut's centreline radius,
#
#     (a - c)^2 - (b + c)^2 = o^2      the radical line standing at x = o
#     a^2 - b^2 - 2c(a + b) = o^2
#     c = o * ((a + b) - o) / (2 * (a + b))
#
# so all three conditions are met by one figure and there is nothing to pick.
#
# Walled to the same BRANCH as A and B, laid either side of that centreline.
# Equal walls then buy here exactly what they bought between A and B: with the
# centrelines tangent, outer meets outer and inner meets inner tangentially too,
# so a strut runs into its rings smoothly instead of crossing them.
STRUT_CL = OFFSET * ((OUTER_CL + HUB_CL) - OFFSET) / (2 * (OUTER_CL + HUB_CL))
STRUT_R = STRUT_CL + BRANCH / 2
STRUT_IR = STRUT_CL - BRANCH / 2
STRUT_DIA = 2 * STRUT_R


def strut_centres():
    """Where a STRUT_R cylinder is tangent to both centrelines.

    Two distance conditions from two known points, so the usual radical-line
    solve: inside A's centreline circle, outside B's.
    """
    d1 = OUTER_CL - STRUT_CL
    d2 = HUB_CL + STRUT_CL
    x = (d1 ** 2 - d2 ** 2 + OFFSET ** 2) / (2 * OFFSET)
    y = math.sqrt(d1 ** 2 - x ** 2)
    return [(x, y), (x, -y)]


STRUTS = strut_centres()

# --- The lip ---------------------------------------------------------------
LIP_WIDTH = 2.0         # radial reach inward, what the light rests on
LIP_HEIGHT = 2.0        # and its thickness
LIP_BORE_R = HUB_IR - LIP_WIDTH
# The light sits on the lip, which fixes the height of its gland and cable.
GLAND_AXIS_Z = LIP_HEIGHT + RING_THICK / 2
RING_TOP_Z = LIP_HEIGHT + RING_THICK    # 15.335, inside the 16

# --- Passthrough -----------------------------------------------------------
GLAND_DIA = specs.figure("led_ring_light", "gland_dia")
CABLE_DIA = specs.figure("led_ring_light", "cable_dia")
GLAND_PROTRUSION = specs.figure("led_ring_light", "gland_protrusion")
CABLE_PROTRUSION = specs.figure("led_ring_light", "cable_protrusion")
PASSTHROUGH_CLEARANCE = specs.figure("fits", "passthrough_radial")
# Measured from +X in the world XY plane, about the hub's own centre. The cutter
# is built in the ring light's frame, where the gland runs along +Y, then turned
# by (this - 90) so the finished exit lands on this bearing.
PASSTHROUGH_ANGLE = 90.0    # y-parallel

# --- Edge breaks -----------------------------------------------------------
TOP_BREAK = 1.0
# The mouth the passthrough opens gets its own, smaller break. At BRANCH 12 the
# pocket sat inside the band and the top edges around it were long enough to
# take the full 1.0; halved to 6 the band is narrower than the 9.64 pocket, so
# the pocket cuts clean through it and leaves a ring of 2.4 to 4.2mm edges whose
# 1.0 breaks run into each other. Same figure the sun lid uses on the same
# feature, for the same reason.
PASSTHROUGH_BREAK = 0.5
# Tried in order. At BRANCH 12 the top face took the full 1.0; halved to 6, with
# MIN_Z_RADIUS halved with it, it will not -- the blends at the crossings are
# only 1.5 wide and the two arcs running into the tangent cusps have no included
# angle to spend. The figure actually used is reported, never assumed.
BREAK_FRACTIONS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3)
# Bottom breaks are for the printer, not for the hand: a 30 degree wall off the
# bed lays down without support where a 45 would droop. Same scheme as the sun
# lid, so the two parts break the same way.
BOTTOM_BREAK_ANGLE = 30.0
BOTTOM_BREAK_SPAN = 2.0
BOTTOM_BREAK_RISE = BOTTOM_BREAK_SPAN / (
    1 + math.tan(math.radians(BOTTOM_BREAK_ANGLE))
)
BOTTOM_BREAK_RUN = BOTTOM_BREAK_SPAN - BOTTOM_BREAK_RISE


def band(inner, outer, height, centre=(0.0, 0.0), z0=0.0):
    return (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .moveTo(*centre)
        .circle(outer)
        .moveTo(*centre)
        .circle(inner)
        .extrude(height)
    )


def rings():
    """A and B, the two struts, and the lip standing under the hub bore."""
    body = band(OUTER_IR, OUTER_R, THICK).union(
        band(HUB_IR, HUB_OR, THICK, centre=(OFFSET, 0.0))
    )
    for centre in STRUTS:
        body = body.union(band(STRUT_IR, STRUT_R, THICK, centre=centre))
    lip = band(LIP_BORE_R, HUB_IR, LIP_HEIGHT, centre=(OFFSET, 0.0))
    return body.union(lip)


# Every circle that bounds mass in plan. A corner can only appear where two of
# them cross, so this is the whole search space.
def boundary_circles():
    return (
        [((0.0, 0.0), OUTER_IR), ((0.0, 0.0), OUTER_R),
         ((OFFSET, 0.0), HUB_IR), ((OFFSET, 0.0), HUB_OR)]
        + [(c, r) for c in STRUTS for r in (STRUT_IR, STRUT_R)]
    )


def crossings():
    """Every point where two boundary circles cross.

    Solved rather than hunted for. With A and B alone there were two; each strut
    adds four more, and picking them off a render is how one gets missed and
    left sharp. Points that no edge lands on cost nothing -- nothing is selected
    there.
    """
    out = []
    circles = boundary_circles()
    for i, (c1, r1) in enumerate(circles):
        for c2, r2 in circles[i + 1:]:
            dx, dy = c2[0] - c1[0], c2[1] - c1[1]
            d = math.hypot(dx, dy)
            # Tangency has to be excluded with room to spare, not to machine
            # epsilon: with every boundary here tangent to some other by
            # construction, a 1e-13 residual would otherwise read as a pair of
            # crossings a nanometre apart and send the filleter after them.
            if d < 1e-6 or d > r1 + r2 - 1e-6 or d < abs(r1 - r2) + 1e-6:
                continue          # concentric, apart, tangent, or nested
            a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
            h = math.sqrt(max(r1 ** 2 - a ** 2, 0.0))
            mx, my = c1[0] + a * dx / d, c1[1] + a * dy / d
            out += [(mx + s * h * dy / d, my - s * h * dx / d) for s in (1, -1)]
    return out


def blend_crossings(shape, radius):
    """Round every vertical corner the union leaves, to MIN_Z_RADIUS.

    All at once if OCC will take them, else one at a time so a single refusal
    does not cost the rest -- with four primitives meeting there are corners
    with very little face to spend, and which ones is worth naming.
    """
    targets = crossings()
    keep = [
        edge
        for edge in shape.edges("|Z").vals()
        if any(math.hypot(edge.Center().x - x, edge.Center().y - y) < 0.6
               for x, y in targets)
    ]
    if not keep:
        return shape, (0, [])

    def blend(base, edges):
        builder = BRepFilletAPI_MakeFillet(base.val().wrapped)
        for edge in edges:
            builder.Add(radius, TopoDS.Edge_s(edge.wrapped))
        builder.Build()
        return cq.Workplane(obj=cq.Shape.cast(builder.Shape()))

    try:
        return blend(shape, keep), (len(keep), [])
    except Exception:
        pass
    good, skipped = [], []
    for edge in keep:
        try:
            blend(shape, [edge])
            good.append(edge)
        except Exception:
            c = edge.Center()
            skipped.append((round(c.x, 2), round(c.y, 2)))
    if not good:
        return shape, (0, skipped)
    return blend(shape, good), (len(good), skipped)


GLAND_R = GLAND_DIA / 2 + PASSTHROUGH_CLEARANCE
CABLE_R = CABLE_DIA / 2 + PASSTHROUGH_CLEARANCE
GLAND_END = RING_OD / 2 + GLAND_PROTRUSION + PASSTHROUGH_CLEARANCE
# Half the outside-to-outside U, less one cable diameter, is the centreline the
# cable can actually be bent around. Cut any tighter and the channel is a kink.
BEND_OD_OD = specs.figure("led_ring_light", "cable_bend_od_od")
BEND_R = (BEND_OD_OD - CABLE_DIA) / 2


def passthrough_cutter():
    """The gland's straight pocket, and the cable's route out of it.

    Built in the ring light's own frame, where the gland protrudes along +Y at
    the ring's mid-thickness -- the convention spec/led_ring_light.md sets --
    then turned to PASSTHROUGH_ANGLE and moved onto the hub's centre.

    The cable leaves the gland straight, then turns up and away on BEND_R and
    runs out through the top face. Swept rather than boxed: a channel that turns
    the cable faster than it bends does not route it, it kinks it, and the
    figure that decides is a property of the cable rather than of the lid.
    """
    gland = (
        cq.Workplane("XZ")
        .workplane(offset=-GLAND_END)
        .center(0, GLAND_AXIS_Z)
        .circle(GLAND_R)
        .extrude(GLAND_END)
    )

    # Straight out to the gland face, a quarter turn up, then clear of the top.
    # The arc's centre sits directly above the point the turn starts, so the
    # mid-point is at 45 degrees round it -- given to threePointArc, which has
    # no sign convention to get wrong.
    y_end = GLAND_END + BEND_R
    z_end = GLAND_AXIS_Z + BEND_R
    path = (
        cq.Workplane("YZ")
        .moveTo(0.0, GLAND_AXIS_Z)
        .lineTo(GLAND_END, GLAND_AXIS_Z)
        .threePointArc(
            (GLAND_END + BEND_R * math.sin(math.pi / 4),
             GLAND_AXIS_Z + BEND_R * (1 - math.cos(math.pi / 4))),
            (y_end, z_end),
        )
        .lineTo(y_end, THICK + 5.0)
    )
    cable = (
        cq.Workplane("XZ", origin=(0.0, 0.0, GLAND_AXIS_Z))
        .circle(CABLE_R)
        .sweep(path, isFrenet=True)
    )

    # Neither body is the cut on its own. Both are dragged straight up +Z and it
    # is the dragged volume that is removed, so the light can still be lowered
    # in from above: the gland and the cable have to pass down through every
    # height over their seated position, and a pocket shaped to where they end
    # up traps them on the way.
    #
    # Dragging a circle straight up gives the circle plus a slab standing on its
    # horizontal diameter -- not a slab from the circle's underside, which is
    # what a bounding box would give and which over-cuts the flanks by a full
    # radius. So each drag starts at its channel's *axis*, and the round part of
    # the section below that comes from the gland cylinder and the swept cable
    # itself. The section stays the component's own circle everywhere it is not
    # the roof.
    top = THICK + 5.0
    gland_up = (
        cq.Workplane("YZ")
        .moveTo(0.0, GLAND_AXIS_Z)
        .lineTo(GLAND_END, GLAND_AXIS_Z)
        .lineTo(GLAND_END, top)
        .lineTo(0.0, top)
        .close()
        .extrude(GLAND_R, both=True)
    )
    # The cable's own path, not an offset of it, for the same reason.
    cable_up = (
        cq.Workplane("YZ")
        .moveTo(0.0, GLAND_AXIS_Z)
        .lineTo(GLAND_END, GLAND_AXIS_Z)
        .threePointArc(
            (GLAND_END + BEND_R * math.sin(math.pi / 4),
             GLAND_AXIS_Z + BEND_R * (1 - math.cos(math.pi / 4))),
            (GLAND_END + BEND_R, GLAND_AXIS_Z + BEND_R),
        )
        .lineTo(GLAND_END + BEND_R, top)
        .lineTo(0.0, top)
        .close()
        .extrude(CABLE_R, both=True)
    )

    cut = gland.union(cable).union(gland_up).union(cable_up)
    return cut.rotate((0, 0, 0), (0, 0, 1), PASSTHROUGH_ANGLE - 90.0).translate(
        (OFFSET, 0, 0)
    )


def lip_edges(solid):
    """Every edge of the lip -- the one feature that keeps its corners.

    The light seats on this ledge and registers against its bore. A break on
    either would turn a flat seat into a line contact and let the ring sit low
    and cocked, so the lip is excluded from both edge treatments.
    """
    marked = []
    for edge in solid.Edges():
        centre = edge.Center()
        r = math.hypot(centre.x - OFFSET, centre.y)
        on_bore = abs(r - LIP_BORE_R) < 0.05
        on_seat = abs(centre.z - LIP_HEIGHT) < 1e-6 and r < HUB_IR + 0.05
        if on_bore or on_seat:
            marked.append(edge.wrapped)
    return marked


class _These(cq.selectors.Selector):
    """Exactly the edges handed to it -- no direction or box filter can express
    'every edge on this face except the lip's'."""

    def __init__(self, edges):
        self.edges = edges

    def filter(self, objectList):
        return [
            o for o in objectList
            if any(o.wrapped.IsSame(e.wrapped) for e in self.edges)
        ]


def _at_z(shape, z):
    return [e for e in shape.val().Edges() if abs(e.Center().z - z) < 1e-6]


def on_passthrough(edge):
    """Is this edge part of the opening the gland cuts?

    Measured off the passthrough's own axis rather than by edge length: short
    edges turn up wherever two blends meet, and length would sweep those in too.
    """
    c = edge.Center()
    v = (c.x - OFFSET, c.y)
    a = math.radians(PASSTHROUGH_ANGLE)
    u = (math.cos(a), math.sin(a))
    along = v[0] * u[0] + v[1] * u[1]
    if along <= 0:
        return False
    perp = math.hypot(v[0] - along * u[0], v[1] - along * u[1])
    return perp < GLAND_DIA / 2 + PASSTHROUGH_CLEARANCE + 1.5


def break_edges(shape):
    """1mm off the top, a printable 30 degree wall off the bottom, lip left alone.

    The lip has to be excluded by name. Its bore runs from z=0 to the seat, so
    its lower edge sits in the bottom selection like any other and a
    BOTTOM_BREAK_RISE break there would eat 1.27 of the 2mm the ring seats
    against -- most of the lip, on the one feature that is holding the light.
    """
    spare = lip_edges(shape.val())

    def keep(edges):
        return [
            e for e in edges
            if not any(e.wrapped.IsSame(other) for other in spare)
        ]

    def run(shape, edges, *lengths):
        """All at once if it will go, else one at a time, reporting refusals.

        A break is a local operation but the builder is not: one edge it cannot
        resolve fails the whole pass, and the pass is most of the part's
        finish. Narrow the band and the crossings come closer together until
        some edge runs out of face to spend, so which edge refuses is a fact
        about the current BRANCH -- worth naming rather than guessing at.
        """
        if not edges:
            return shape, 0, []
        try:
            return shape.edges(_These(edges)).chamfer(*lengths), len(edges), []
        except Exception:
            pass
        done, skipped = [], []
        for edge in edges:
            try:
                shape.edges(_These([edge])).chamfer(*lengths)
                done.append(edge)
            except Exception:
                c = edge.Center()
                skipped.append((round(c.x, 2), round(c.y, 2), round(c.z, 2)))
        if not done:
            return shape, 0, skipped
        return shape.edges(_These(done)).chamfer(*lengths), len(done), skipped

    def largest(shape, edges, *lengths):
        """The biggest fraction of `lengths` the whole set will take.

        Uniform, not per-edge. A break that lands 1.0 on the long arcs and 0.5
        on the short ones looks like a mistake on the finished part, and the
        edges that refuse are the conspicuous ones -- the blends at the
        crossings, and the two arcs running into the tangent cusps. Better one
        honest figure, reported, than a hidden mixture.
        """
        if not edges:
            return shape, 0.0
        for f in BREAK_FRACTIONS:
            try:
                return shape.edges(_These(edges)).chamfer(*[f * n for n in lengths]), f
            except Exception:
                continue
        return shape, 0.0

    top = keep(_at_z(shape, THICK))
    shape, f_top = largest(shape, top, TOP_BREAK)
    used_top = f_top * TOP_BREAK
    n_top, skip_top = (len(top), []) if used_top else (0, ["none would build"])

    # Re-read after the top pass: chamfering rebuilt the solid, so edges taken
    # before it are no longer the ones in this shape.
    spare = lip_edges(shape.val())
    bottom = keep(_at_z(shape, 0.0))
    shape, f_bot = largest(shape, bottom, BOTTOM_BREAK_RUN, BOTTOM_BREAK_RISE)
    used_bot = f_bot * BOTTOM_BREAK_SPAN
    n_bottom = len(bottom) if used_bot else 0
    return shape, (n_top, skip_top, used_top), (n_bottom, [], used_bot)


def build():
    body = rings()
    body, blended = blend_crossings(body, MIN_Z_RADIUS)
    # Broken before the passthrough, not after. The break belongs to the lid's
    # own outline, and letting the gland cut come first made it compete for the
    # same millimetre: the channel mouth left 2 to 4mm edges whose 1mm breaks
    # ran into each other, and the whole face dropped to 0.70 to accommodate a
    # feature that is a clearance hole. Cut afterwards, the channel simply
    # crosses a finished chamfer and leaves its own mouth square.
    body, n_top, n_bottom = break_edges(body)
    body = body.cut(passthrough_cutter())
    # Turned as a whole, last: the part is laid out about +X because that is
    # where the tangency is easiest to reason about, and where it ends up
    # pointing is a separate question from how it is built.
    return body.rotate((0, 0, 0), (0, 0, 1), PART_ROTATION), blended, n_top, n_bottom


eclipse, BLENDED, N_TOP, N_BOTTOM = build()

if __name__ == "__main__":
    show_object(eclipse, name="eclipse_lid",
                options={"color": (250, 190, 60), "alpha": 1.0}, clear=True)

    dx, dy, dz = print_volume.extents(eclipse)
    print(f"mouth band   {2 * OUTER_IR:.1f} .. {2 * OUTER_R:.1f} dia "
          f"(seats in {MOUTH_ID:g} at {MOUTH_FIT:g} allowance)")
    print(f"hub band     {2 * HUB_IR:.1f} .. {2 * HUB_OR:.1f} dia "
          f"(bore {HUB_BORE:g} over {RING_OD:.4f} OD)")
    print(f"centrelines  {OUTER_CL:.2f} and {HUB_CL:.2f}, offset {OFFSET:.2f} "
          f"-- tangent, {OUTER_CL - (OFFSET + HUB_CL):+.3f} apart")
    print(f"branch       {BRANCH:g} wide, {THICK:g} thick")
    print(f"lip          {LIP_WIDTH:g} reach x {LIP_HEIGHT:g} high, bore "
          f"{2 * LIP_BORE_R:.1f}; ring top sits at z {RING_TOP_Z:.3f}")
    _t = math.radians(PART_ROTATION)
    _placed = [
        (x * math.cos(_t) - y * math.sin(_t), x * math.sin(_t) + y * math.cos(_t))
        for x, y in STRUTS
    ]
    print(f"struts       2 x {STRUT_DIA:.3f} dia, {2 * STRUT_IR:.3f} bore "
          f"({BRANCH:g} wall) at "
          + " and ".join(f"({x:.3f}, {y:+.3f})" for x, y in _placed))
    print(f"turned       {PART_ROTATION:+g} deg about +Z; hub centre now at "
          f"({-OFFSET * math.sin(_t) * 0 + OFFSET * math.cos(_t):.2f}, "
          f"{OFFSET * math.sin(_t):.2f}), gland exit "
          f"{(PASSTHROUGH_ANGLE + PART_ROTATION) % 360:g} deg from +X")
    print(f"             centreline r {STRUT_CL:.4f}, centres on the gland axis "
          f"x={OFFSET:.2f} to {max(abs(x - OFFSET) for x, _y in STRUTS):.1e} mm")
    # Tangency of centreline to centreline is the thing to check, so check it:
    # the distance between two tangent circles' centres is the sum of the radii
    # or the difference, and nothing else.
    sx, sy = STRUTS[0]
    for name, cl, (cx, cy) in (("A", OUTER_CL, (0.0, 0.0)),
                               ("B", HUB_CL, (OFFSET, 0.0))):
        d = math.hypot(sx - cx, sy - cy)
        err = min(abs(d - abs(cl - STRUT_CL)), abs(d - (cl + STRUT_CL)))
        print(f"             centreline tangent to {name}: off by {err:.1e} mm")
    print(f"corners      {BLENDED[0]} blended to R{MIN_Z_RADIUS:g}"
          + (f"  -- REFUSED at {BLENDED[1]}" if BLENDED[1] else ""))
    print(f"breaks       {N_TOP[0]} top at {N_TOP[2]:.2f}"
          + ("" if abs(N_TOP[2] - TOP_BREAK) < 1e-9
             else f"  <-- {TOP_BREAK:g} asked for, would not build"))
    print(f"             {N_BOTTOM[0]} bottom, {N_BOTTOM[2]:.2f} span at 30 deg"
          + ("" if abs(N_BOTTOM[2] - BOTTOM_BREAK_SPAN) < 1e-9
             else f"  <-- {BOTTOM_BREAK_SPAN:g} asked for"))
    print(f"cable        bend R{BEND_R:.3f} centreline (from {BEND_OD_OD:g} OD-OD), "
          f"turns up at y {GLAND_END:.2f}, exits top")
    print(f"extent       {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(eclipse.val().Solids())} body, "
          f"{eclipse.val().Volume() / 1000:.1f} cm3")
    print(f"bed          {'fits' if print_volume.fits(eclipse) else 'DOES NOT FIT'}")
