# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Vessel 3 Eclipse -- vessel_2_eclipse/eclipse.py cut to Vessel 3's mouth.

Saved as from Vessel 2's on 2026-09-10, when Vessel 3 was opened at a 112mm
top opening. Same design, same two bands tangent at one point, same absent
struts; only the mouth changed, and everything downstream of it followed.

## Why the struts are still not needed

eclipse_lid/eclipse.py adds two more circles (C and D, tangent to both band
centrelines, mirrored off the x-axis) as extra reinforcement beyond the join
the two bands already make where the hub band's outer circle crosses the
mouth band's inner circle. That join has to be a real lens, not a tangent
point, or the struts come back.

It survives the smaller mouth, but with less to spare: OUTER_IR=50, HUB_OR
=50.5, offset 5.5 -- |50-50.5|=0.5 < 5.5 < 100.5, so the circles still cross
and the union is still one connected solid. The margin at the lower bound is
0.5mm against Vessel 2's 2.5mm and Vessel 1's 14.75mm, because the mouth
band closed in on a hub band that did not move: the hub is set by LED Ring
Light 2, which is the same light on both vessels.

## What the tighter mouth costs

Two things worth knowing before this is printed, neither of them fatal:

- The crescent -- the open sweep that makes it read as an eclipse -- falls
  from 11mm to 5mm at its widest (180 degrees from the hub centre). It is
  still open, and still the widest part of the part, which is why the cable
  still exits there.
- The cable's bend route ends 1.49mm clear of the mouth band's inner wall,
  where on Vessel 2 it had 7.49mm. The route is a clearance cut around
  something flexible, not a fit, so this is tolerance to watch rather than
  interference to fix -- but it is the first dimension here that would go
  negative if the mouth shrank again, and PASSTHROUGH_ANGLE is the thing to
  reach for if it does.

## What drives what

Same rule as eclipse_lid/eclipse.py: nothing here is a chosen diameter. The
outer band is Vessel 3's top opening (spec/vessel_3.md, seated with no
allowance per spec/fits.md) and the inner band is the 89.0mm slip bore for
LED Ring Light 2. The offset falls out of those two and BRANCH.

Note that spec/vessel_3.md does not yet call its 112 confirmed. This part is
cut to a working figure, so treat a first print of it as a fit test that
happens to be a lid.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import print_volume
import specs
from cadkit.engrave import engrave_radial_text
from cadkit.viewer import show as show_object
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS

OUTPUT_DIR = Path(__file__).parent / "output"

PART_ROTATION = 90.0    # about +Z, right hand, applied to the finished body
THICK = 16.0            # z -- unchanged from eclipse_lid
BRANCH = 6.0            # radial width of both bands
MIN_Z_RADIUS = 1.5      # least radius allowed about a vertical axis

# --- The two bands ---------------------------------------------------------
MOUTH_ID = specs.figure("vessel_3", "top_opening_id")
MOUTH_FIT = specs.figure("fits", "vessel_mouth_radial")
RING_SPEC = "led_ring_light_2"
RING_OD = specs.figure(RING_SPEC, "ring_od")
RING_THICK = specs.figure(RING_SPEC, "ring_thickness")
HUB_BORE = RING_OD + 2 * specs.figure("fits", "ring_light_bore_radial")

OUTER_R = MOUTH_ID / 2 - MOUTH_FIT      # 56.0
OUTER_IR = OUTER_R - BRANCH             # 50.0
HUB_IR = HUB_BORE / 2                   # 44.50
HUB_OR = HUB_IR + BRANCH                # 50.50

# Centrelines, and the offset that makes them touch.
OUTER_CL = (OUTER_R + OUTER_IR) / 2     # 53.00
HUB_CL = (HUB_IR + HUB_OR) / 2          # 47.50
OFFSET = OUTER_CL - HUB_CL              # 5.50, along +X -- 8.50 on Vessel 2

# --- The lip ---------------------------------------------------------------
LIP_WIDTH = 2.0         # radial reach inward, what the light rests on
LIP_HEIGHT = 2.0        # and its thickness
LIP_BORE_R = HUB_IR - LIP_WIDTH
GLAND_AXIS_Z = LIP_HEIGHT + RING_THICK / 2
RING_TOP_Z = LIP_HEIGHT + RING_THICK    # 15.335, inside the 16

# --- Passthrough -----------------------------------------------------------
GLAND_DIA = specs.figure(RING_SPEC, "gland_dia")
CABLE_DIA = specs.figure(RING_SPEC, "cable_dia")
GLAND_PROTRUSION = specs.figure(RING_SPEC, "gland_protrusion")
CABLE_PROTRUSION = specs.figure(RING_SPEC, "cable_protrusion")
PASSTHROUGH_CLEARANCE = specs.figure("fits", "passthrough_radial")
PASSTHROUGH_ANGLE = 180.0   # -X from the hub centre, directly away from the
# tangent points (both at angle 0, +X -- see module docstring). Inherited from
# vessel_2_eclipse, which changed it from eclipse_lid/eclipse.py's 90 at
# Brendan's request (2026-09-01), so the cable exits into the widest part of
# the crescent instead of across it. The widest part is narrower here -- see
# the docstring -- which makes this choice matter more, not less.

# --- Retaining lip on the OD ------------------------------------------------
# Nothing else stops this lid sliding straight through the mouth and dropping
# into the tank: the mouth band is cut to the vessel's ID with zero clearance
# (MOUTH_FIT), so it slides freely at every height. This flange stands proud
# of OUTER_R and catches the rim from above, the same role the stop lip on
# test_fits/tube.py plays for that part -- same radial reach (4mm, tube.py's
# LIP_WIDTH), but 2mm thick rather than that file's 1mm (Brendan's request,
# 2026-09-01).
#
# It extends OUTWARD from OUTER_R, in the top OD_LIP_THICKNESS slice of the
# band's own THICK, not upward on top of it -- the part does not get any
# taller. A first attempt stacked a separate cylinder above THICK instead and
# got corrected (Brendan, 2026-09-01): the lip should extend out from the
# primary OD, not add height. Built in build() before blend_crossings and
# break_edges run, not after, per the same correction -- cosmetic chamfers
# and fillets come last, against the final shape, not tacked onto one that
# already has them.
OD_LIP_WIDTH = 4.0
OD_LIP_THICKNESS = 2.0

# --- Edge breaks -----------------------------------------------------------
TOP_BREAK = 1.0
# Defined but not wired up to anything -- same as in eclipse_lid/eclipse.py.
# A chamfer here was tried and reverted 2026-09-01: sizing it against the
# cut's own edges kept landing on real pairwise conflicts (two edges each
# fine alone, incompatible chamfered together at a shared vertex), and the
# fix attempts got more fragile, not less, without actually converging on
# what Brendan's photo was pointing at. Worth another pass with the photo in
# hand before trying again, not blind.
PASSTHROUGH_BREAK = 0.5
BREAK_FRACTIONS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3)
BOTTOM_BREAK_ANGLE = 30.0
BOTTOM_BREAK_SPAN = 2.0
BOTTOM_BREAK_RISE = BOTTOM_BREAK_SPAN / (
    1 + math.tan(math.radians(BOTTOM_BREAK_ANGLE))
)
BOTTOM_BREAK_RUN = BOTTOM_BREAK_SPAN - BOTTOM_BREAK_RISE

# --- Labels ------------------------------------------------------------
# Engraved, never raised -- a boss would fatten the OD or pinch the bore it
# labels, see cadkit.engrave. Both sit at mid-height on the flat vertical band,
# clear of the top chamfer and bottom break.
LABEL_Z = THICK / 2
# Total OD at the top of the part (theta=90 deg), clear of the tangent points
# (both at 0 deg, see module docstring) and the two blended corners that sit
# near them. Ring light diameter at the bottom of the hub bore (theta=-90),
# clear of the same tangent zone and of the passthrough pocket at 180.
OD_LABEL_THETA = math.pi / 2
HUB_LABEL_THETA = -math.pi / 2


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
    """A and B, and the lip standing under the hub bore. No struts."""
    body = band(OUTER_IR, OUTER_R, THICK).union(
        band(HUB_IR, HUB_OR, THICK, centre=(OFFSET, 0.0))
    )
    lip = band(LIP_BORE_R, HUB_IR, LIP_HEIGHT, centre=(OFFSET, 0.0))
    return body.union(lip)


# Every circle that bounds mass in plan. A corner can only appear where two of
# them cross, so this is the whole search space.
def boundary_circles():
    return [
        ((0.0, 0.0), OUTER_IR), ((0.0, 0.0), OUTER_R),
        ((OFFSET, 0.0), HUB_IR), ((OFFSET, 0.0), HUB_OR),
    ]


def crossings():
    """Every point where two boundary circles cross. Solved, not hunted for."""
    out = []
    circles = boundary_circles()
    for i, (c1, r1) in enumerate(circles):
        for c2, r2 in circles[i + 1:]:
            dx, dy = c2[0] - c1[0], c2[1] - c1[1]
            d = math.hypot(dx, dy)
            if d < 1e-6 or d > r1 + r2 - 1e-6 or d < abs(r1 - r2) + 1e-6:
                continue          # concentric, apart, tangent, or nested
            a = (r1 ** 2 - r2 ** 2 + d ** 2) / (2 * d)
            h = math.sqrt(max(r1 ** 2 - a ** 2, 0.0))
            mx, my = c1[0] + a * dx / d, c1[1] + a * dy / d
            out += [(mx + s * h * dy / d, my - s * h * dx / d) for s in (1, -1)]
    return out


def blend_crossings(shape, radius):
    """Round every vertical corner the union leaves, to MIN_Z_RADIUS."""
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
BEND_OD_OD = specs.figure(RING_SPEC, "cable_bend_od_od")
BEND_R = (BEND_OD_OD - CABLE_DIA) / 2


def passthrough_cutter():
    """The gland's straight pocket, and the cable's route out of it."""
    gland = (
        cq.Workplane("XZ")
        .workplane(offset=-GLAND_END)
        .center(0, GLAND_AXIS_Z)
        .circle(GLAND_R)
        .extrude(GLAND_END)
    )

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
    """Every edge of the lip -- the one feature that keeps its corners."""
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
    """Exactly the edges handed to it."""

    def __init__(self, edges):
        self.edges = edges

    def filter(self, objectList):
        return [
            o for o in objectList
            if any(o.wrapped.IsSame(e.wrapped) for e in self.edges)
        ]


def _at_z(shape, z):
    return [e for e in shape.val().Edges() if abs(e.Center().z - z) < 1e-6]


def break_edges(shape):
    """A 45 degree cosmetic break and a printable 30 degree DFM break, lip
    left alone -- swapped from which z they sit at, not from what they are.

    Brendan flipped this part's print orientation 2026-09-01 (the OD lip
    made the original orientation less printable) via a 180 degree rotation
    in build(), applied after this function returns. z=THICK here ends up
    as the new physical bottom, touching the bed; z=0 ends up as the new
    physical top. So the shallow, overhang-friendly DFM break belongs on
    z=THICK now, and the plain symmetric 45 degree break belongs on z=0 --
    the reverse of where they sat before the flip was requested.
    """
    spare = lip_edges(shape.val())

    def keep(edges):
        return [
            e for e in edges
            if not any(e.wrapped.IsSame(other) for other in spare)
        ]

    def run(shape, edges, *lengths):
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
        if not edges:
            return shape, 0.0
        for f in BREAK_FRACTIONS:
            try:
                return shape.edges(_These(edges)).chamfer(*[f * n for n in lengths]), f
            except Exception:
                continue
        return shape, 0.0

    # The old top rim at OUTER_R is gone by the time this runs: the OD
    # retaining lip (added in build(), before this function) fuses flush onto
    # it in the same z=THICK plane, so that edge disappears into one
    # continuous flat face rather than surviving as a corner -- the DFM break
    # below applies to the lip's own outer edge (OUTER_R + OD_LIP_WIDTH) like
    # any other z=THICK edge, no exclusion needed.
    #
    # z=THICK: new physical bottom after the flip -- DFM break.
    z_thick = keep(_at_z(shape, THICK))
    shape, f_thick = largest(shape, z_thick, BOTTOM_BREAK_RUN, BOTTOM_BREAK_RISE)
    used_thick = f_thick * BOTTOM_BREAK_SPAN
    n_thick, skip_thick = (
        (len(z_thick), []) if used_thick else (0, ["none would build"])
    )

    # z=0: new physical top after the flip -- plain 45 degree break.
    spare = lip_edges(shape.val())
    z_zero = keep(_at_z(shape, 0.0))
    shape, f_zero = largest(shape, z_zero, TOP_BREAK)
    used_zero = f_zero * TOP_BREAK
    n_zero = len(z_zero) if used_zero else 0

    return shape, (n_thick, skip_thick, used_thick), (n_zero, [], used_zero)


def build():
    body = rings()

    # Steps out from OUTER_R to OUTER_R + OD_LIP_WIDTH, in the top
    # OD_LIP_THICKNESS slice of the band's own height -- not above THICK, see
    # the constant's own comment. The step's vertical face (r=OUTER_R,
    # z=THICK-OD_LIP_THICKNESS..THICK) is a real shared face with the wall's
    # existing outer surface there, not just a touching edge, so the union
    # fuses into one solid.
    od_lip = band(
        OUTER_R, OUTER_R + OD_LIP_WIDTH, OD_LIP_THICKNESS,
        z0=THICK - OD_LIP_THICKNESS,
    )
    body = body.union(od_lip)

    body, blended = blend_crossings(body, MIN_Z_RADIUS)
    body, n_top, n_bottom = break_edges(body)

    body = body.cut(passthrough_cutter())

    body = engrave_radial_text(
        body, f"{MOUTH_ID:g}", OUTER_R, +1, LABEL_Z, theta0=OD_LABEL_THETA
    )
    body = engrave_radial_text(
        body, f"{HUB_BORE:g}", HUB_IR, -1, LABEL_Z, theta0=HUB_LABEL_THETA,
        centre=(OFFSET, 0.0),
    )

    body = body.rotate((0, 0, 0), (0, 0, 1), PART_ROTATION)

    # Print orientation flip (Brendan, 2026-09-01): the OD lip made the
    # original orientation (mouth band's own top, with the lip, up) less
    # printable, so the part is turned upside down for the bed. A rotation
    # 180 degrees about an in-plane axis, not a mirror -- a true mirror
    # reflects chirality, which would flip the engraved digits into their
    # own mirror image; a rotation carries them over readable. break_edges
    # already swapped which break style sits at which z to match, so nothing
    # else here needs to know the part is now upside down.
    body = body.rotate((0, 0, 0), (1, 0, 0), 180)
    body = body.translate((0, 0, -body.val().BoundingBox().zmin))

    return body, blended, n_top, n_bottom


eclipse, BLENDED, N_TOP, N_BOTTOM = build()

# Display upright while retaining the bed orientation in `eclipse` for export.
display_eclipse = eclipse.rotate((0, 0, 0), (1, 0, 0), 180)
display_eclipse = display_eclipse.translate(
    (0, 0, -display_eclipse.val().BoundingBox().zmin)
)
display_eclipse = display_eclipse.rotate((0, 0, 0), (0, 0, 1), -90)

if __name__ == "__main__":
    show_object(display_eclipse, name="vessel_3_eclipse",
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
    print(f"corners      {BLENDED[0]} blended to R{MIN_Z_RADIUS:g}"
          + (f"  -- REFUSED at {BLENDED[1]}" if BLENDED[1] else ""))
    print(f"breaks       {N_TOP[0]} at z=THICK (new bottom, printed against the "
          f"bed), {N_TOP[2]:.2f} span at 30 deg DFM"
          + ("" if abs(N_TOP[2] - BOTTOM_BREAK_SPAN) < 1e-9
             else f"  <-- {BOTTOM_BREAK_SPAN:g} asked for"))
    print(f"             {N_BOTTOM[0]} at z=0 (new top, cosmetic), "
          f"{N_BOTTOM[2]:.2f} at 45 deg"
          + ("" if abs(N_BOTTOM[2] - TOP_BREAK) < 1e-9
             else f"  <-- {TOP_BREAK:g} asked for, would not build"))
    print(f"cable        bend R{BEND_R:.3f} centreline (from {BEND_OD_OD:g} OD-OD), "
          f"turns up at y {GLAND_END:.2f}, exits top")
    print(f"extent       {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(eclipse.val().Solids())} body, "
          f"{eclipse.val().Volume() / 1000:.1f} cm3")
    print(f"bed          {'fits' if print_volume.fits(eclipse) else 'DOES NOT FIT'}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(eclipse, str(OUTPUT_DIR / "vessel_3_eclipse.step"))
