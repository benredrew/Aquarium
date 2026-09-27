# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Lamp Shade lid -- Vessel 1's mouth at the bottom, LED Ring Light 1 at the
top, and a programmable surface of revolution in between.

The two ends are not new. The bottom is the same cylindrical face every part
that seats in this vessel has used since the LED Sun Lid: cut directly to the
167mm top opening with nothing added (spec/fits.md, `vessel_mouth_radial` = 0),
with an outward flange above it so the part catches the rim instead of sliding
through -- the lesson vessel_2_eclipse learned the hard way. The top is the
same ring-light interface: an 89.5mm bore over the ring's 89.3572mm OD, with a
2mm lip at its bottom for the light to rest on, and a passthrough cut as the
*vertical sweep* of the gland and cable rather than their seated envelope,
because the light is installed by dropping it in from above.

What is new is the middle, and the way the middle is described.

## The profile is the design

The shade is one closed section revolved about Z. Its two conical faces are not
written as geometry; they are sampled from `SHADE_PROFILE`, a function of one
parameter `u` running 0 at the brim to 1 at the hub, returning how far along
its travel the radius has gone. The default is `cone` -- `lambda u: u`, a
straight line, which revolves to an exact cone however many samples are asked
for, because collinear samples are dropped before the wire is drawn. Swap in
`ogee` or `bell` below and *both* faces follow the same curve, so the wall
stays sane without either face being dimensioned separately.

The endpoints are the part's job, not the profile's. Outer runs BRIM_R to
HUB_OR; inner runs SHADE_IR0 to HUB_IR. Every one of those is fixed by an
interface or by the wall thickness, so a new profile can change the silhouette
without being able to change a fit.
That is the whole point of putting the shape behind a function: the numbers
that matter are out of its reach.

## The overhang, which is real

A 16mm shade spanning 36.75mm of radius puts both conical faces at 66.5 degrees
from vertical -- 23.5 from horizontal. That is well past what FDM bridges, and
it is inherent to the proportions rather than to this model: only a taller
shade fixes it. Printed as modelled, cylinder on the bed, the overhanging face
is the *inner* one, which is the right trade -- the visible outer cone tapers
inward as it rises and prints clean, and the droop is inside where the water
and the light are. Flipping the part swaps which face suffers and ruins the one
you look at.

Run the script; it prints the wall angle and the shade height that would bring
both faces to 45 degrees.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import drawing
import print_volume
import specs
from cadquery.selectors import Selector
from engrave import engrave_radial_text
from ocp_vscode import set_port, show_object

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Interfaces ------------------------------------------------------------
# Read, never retyped. The vessel document says 167 and the ring light document
# says 89.3572; this file says neither.
VESSEL_TOP_ID = specs.figure("vessel", "top_opening_id")
MOUTH_FIT = specs.figure("fits", "vessel_mouth_radial")

RING_SPEC = "led_ring_light"
RING_OD = specs.figure(RING_SPEC, "ring_od")
RING_THICK = specs.figure(RING_SPEC, "ring_thickness")
GLAND_DIA = specs.figure(RING_SPEC, "gland_dia")
GLAND_PROTRUSION = specs.figure(RING_SPEC, "gland_protrusion")
CABLE_DIA = specs.figure(RING_SPEC, "cable_dia")
BEND_OD_OD = specs.figure(RING_SPEC, "cable_bend_od_od")
HUB_BORE = RING_OD + 2 * specs.figure("fits", "ring_light_bore_radial")  # 89.5

# --- Design parameters -----------------------------------------------------
WALL = 6.0              # hub wall, and the shade's wall at the hub end
SEAT_H = 8.0            # how far the cylinder hangs into the mouth
FLANGE_REACH = 4.0      # outward catch on the rim, as vessel_2_eclipse's OD lip
FLANGE_H = 2.0
SHADE_H = 16.0          # brim to hub -- the dial Brendan set 2026-09-26
HUB_H = 16.0            # lip + ring + a little, same as the Eclipse's THICK
LIP_WIDTH = 2.0         # what the light rests on
LIP_HEIGHT = 2.0
SHADE_STEPS = 24        # samples taken across the profile. Collinear ones are
                        # dropped (drop_collinear), so a straight profile comes
                        # out as one exact segment whatever this is set to and
                        # only a curve actually spends them.

# --- Derived radii and heights ---------------------------------------------
SEAT_R = VESSEL_TOP_ID / 2 - MOUTH_FIT      # 83.50, seats in the mouth
SEAT_IR = SEAT_R - WALL                     # 77.50
BRIM_R = SEAT_R + FLANGE_REACH              # 87.50

# Where the shade's inner face starts, at the brim. Its top end is not a choice
# -- it is the ring light's bore -- so this is the only handle on how heavy the
# shade is, and it is worth understanding before it is turned.
#
# At SEAT_IR the inner face runs on from the cylinder bore with no step at all,
# and the wall comes out 10mm measured horizontally. On a face this steep that
# is not 10mm of plastic: perpendicular to the cone it is 4.0mm at the brim
# tapering to 2.4mm at the hub, which is a sane shell. It is still the heaviest
# version, because the extra sits where the part is widest.
#
# At BRIM_R - WALL (81.50) the horizontal wall is a constant 6mm and the normal
# thickness a constant 2.4mm. Measured, that is 116.8cm3 down to 103.1 -- 12%
# off the whole part, not the third the shade section alone might suggest,
# because two thirds of this part is cylinder, flange and hub and none of that
# moves. The cost is a 4mm ledge at z=SHADE_Z0 where the cylinder bore meets
# the shade -- which is free here: printed cylinder-down that ledge faces *up*,
# so it is supported, unlike almost every other step in this part.
SHADE_IR0 = SEAT_IR
HUB_IR = HUB_BORE / 2                       # 44.75, ring light drops in here
HUB_OR = HUB_IR + WALL                      # 50.75
LIP_BORE_R = HUB_IR - LIP_WIDTH             # 42.75

SHADE_Z0 = SEAT_H + FLANGE_H                # 10.0, top of the flange
SHADE_Z1 = SHADE_Z0 + SHADE_H               # 26.0, bottom of the hub
SEAT_Z = SHADE_Z1 + LIP_HEIGHT              # 28.0, the face the light lands on
TOP_Z = SHADE_Z1 + HUB_H                    # 42.0
RING_TOP_Z = SEAT_Z + RING_THICK            # 41.335, inside TOP_Z

# The light rests on the lip, which fixes the height of its gland and cable.
GLAND_AXIS_Z = SEAT_Z + RING_THICK / 2      # 34.6675
PASSTHROUGH_CLEARANCE = specs.figure("fits", "passthrough_radial")
PASSTHROUGH_ANGLE = 90.0    # +Y. The cutters are built along +Y, so this is
                            # the identity; the part is axisymmetric, so unlike
                            # the Eclipse lids no angle here is better than any
                            # other and nothing downstream depends on it.

GLAND_R = GLAND_DIA / 2 + PASSTHROUGH_CLEARANCE
CABLE_R = CABLE_DIA / 2 + PASSTHROUGH_CLEARANCE
GLAND_END = RING_OD / 2 + GLAND_PROTRUSION + PASSTHROUGH_CLEARANCE  # 46.9566
BEND_R = (BEND_OD_OD - CABLE_DIA) / 2       # 7.3025 centreline

# --- Edge breaks -----------------------------------------------------------
# The bed-side break is the overhanging one on an FDM printer, so it is cut
# shallower than the 45 degrees a symmetric chamfer would give. Measured from
# vertical: 45 is the usual printable limit, 30 leaves margin. Its two legs
# sum to BED_BREAK_SPAN, matching what a symmetric break elsewhere spends.
BED_BREAK_ANGLE = 30.0
BED_BREAK_SPAN = 2.0
BED_BREAK_RISE = BED_BREAK_SPAN / (1 + math.tan(math.radians(BED_BREAK_ANGLE)))
BED_BREAK_RUN = BED_BREAK_SPAN - BED_BREAK_RISE
FLANGE_FILLET = 1.0     # reentrant corner under the flange; costs bearing face
BRIM_BREAK = 1.0        # the flange's own outer top corner
TOP_BREAK = 1.0         # hub top, cosmetic and handling
BREAK_FRACTIONS = (1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3)

# --- Labels ----------------------------------------------------------------
# Engraved, never raised: a boss on either of these walls would corrupt the fit
# it names. See engrave.py.
SEAT_LABEL_Z = SEAT_H / 2
HUB_LABEL_Z = (SEAT_Z + TOP_Z) / 2
SEAT_LABEL_THETA = -math.pi / 2     # -Y, opposite the passthrough at +Y
HUB_LABEL_THETA = -math.pi / 2


# --- The programmable bit --------------------------------------------------
def cone(u):
    """A straight taper. u in [0, 1], brim to hub; returns fraction travelled."""
    return u


def ogee(u):
    """S-curve: leaves the brim vertical, arrives at the hub vertical."""
    return u * u * (3.0 - 2.0 * u)


def bell(u):
    """Flares hard off the brim, then straightens -- a quarter-sine."""
    return math.sin(u * math.pi / 2)


# The surface of revolution. Change this line -- and raise SHADE_STEPS above 1
# for anything that is not a straight line -- and nothing else moves.
SHADE_PROFILE = cone


FLAT_TOL = 1e-6     # a sample this close to the chord is not a sample


def drop_collinear(pts):
    """Thin out samples that lie on the line their neighbours already draw.

    Without this, `cone` at any SHADE_STEPS above 1 is a silent disaster
    rather than a no-op: the samples are collinear, `polyline` emits them as
    a run of touching segments, and the revolve of that run comes back as a
    solid whose bounding box is infinite and whose volume reads 284cm3 for a
    part that is actually 117. It builds, it shows, and only `print_volume`
    notices -- which is far too late to find out.

    Filtering here rather than warning in a docstring makes SHADE_STEPS safe
    to leave at whatever the last profile needed. A straight run emits one
    segment whatever it is set to, and a curve keeps every sample that bends.
    """
    kept = [pts[0]]
    for i in range(1, len(pts) - 1):
        (r0, z0), (r1, z1), (r2, z2) = kept[-1], pts[i], pts[i + 1]
        chord = math.hypot(r2 - r0, z2 - z0)
        if chord < FLAT_TOL:
            continue
        # Twice the triangle's area over its base is the height of the middle
        # point above the chord the other two draw.
        off = abs((r1 - r0) * (z2 - z0) - (z1 - z0) * (r2 - r0)) / chord
        if off > FLAT_TOL:
            kept.append(pts[i])
    kept.append(pts[-1])
    return kept


def shade_points(r0, r1):
    """The profile sampled between two radii, as (r, z) from brim to hub.

    The endpoints are substituted in exactly rather than evaluated, so a
    profile that is sloppy at u=0 or u=1 still cannot shift an interface.
    """
    pts = []
    for i in range(SHADE_STEPS + 1):
        u = i / SHADE_STEPS
        z = SHADE_Z0 + u * SHADE_H
        if i == 0:
            pts.append((r0, z))
        elif i == SHADE_STEPS:
            pts.append((r1, z))
        else:
            pts.append((r0 + SHADE_PROFILE(u) * (r1 - r0), z))
    return drop_collinear(pts)


def section():
    """The closed half-section, counter-clockwise in (r, z), revolved about Z.

    Outer wall from the bottom up, across the hub's top face, down the bore to
    the lip, then back down the inner cone to the cylinder bore.
    """
    outer = shade_points(BRIM_R, HUB_OR)
    inner = shade_points(SHADE_IR0, HUB_IR)

    pts = [
        (SEAT_IR, 0.0),         # bottom annular face, inner corner
        (SEAT_R, 0.0),          # ... outer corner
        (SEAT_R, SEAT_H),       # the cylinder that goes into the mouth
        (BRIM_R, SEAT_H),       # flange underside -- what beds on the rim
        (BRIM_R, SHADE_Z0),     # flange outer wall
    ]
    pts += outer[1:]            # up the outer cone (brim point already placed)
    pts += [
        (HUB_OR, TOP_Z),        # hub outer wall
        (HUB_IR, TOP_Z),        # hub top face, in to the bore
        (HUB_IR, SEAT_Z),       # down the bore to the lip
        (LIP_BORE_R, SEAT_Z),   # the lip's top face -- the light lands here
        (LIP_BORE_R, SHADE_Z1), # the lip's inner wall
    ]
    pts += list(reversed(inner))    # the lip's underside, then down the inner
                                    # cone
    if abs(SHADE_IR0 - SEAT_IR) > 1e-9:
        pts.append((SEAT_IR, SHADE_Z0))     # the ledge back in to the bore
    return pts


def body():
    pts = section()
    wire = cq.Workplane("XZ").polyline([(r, z) for r, z in pts]).close()
    return wire.revolve(360.0, (0, 0, 0), (0, 1, 0))


# --- Passthrough -----------------------------------------------------------
def passthrough_cutter():
    """The gland's straight pocket, and the cable's route up and out the top.

    Carried over from vessel_3_eclipse/eclipse.py, which took it from the LED
    Sun Lid, and for the same reason in all three: the light drops into the
    bore from above, so what has to be cut is the *vertical sweep* of the gland
    and cable, not the envelope they occupy once seated. An envelope-shaped
    pocket traps the gland on the way in.

    The pocket stays inside the hub wall -- GLAND_END is 46.96 against a
    HUB_OR of 50.75 -- so the cable surfaces through the hub's top annular
    face rather than breaking the OD.
    """
    top = TOP_Z + 5.0

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
        .lineTo(y_end, top)
    )
    cable = (
        cq.Workplane("XZ", origin=(0.0, 0.0, GLAND_AXIS_Z))
        .circle(CABLE_R)
        .sweep(path, isFrenet=True)
    )

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
    return cut.rotate((0, 0, 0), (0, 0, 1), PASSTHROUGH_ANGLE - 90.0)


# --- Edge breaks -----------------------------------------------------------
class These(Selector):
    """Exactly the edges handed to it."""

    def __init__(self, edges):
        self.edges = edges

    def filter(self, objectList):
        return [
            o for o in objectList
            if any(o.wrapped.IsSame(e.wrapped) for e in self.edges)
        ]


def ring_edge(shape, z, r):
    """The circular edge at height `z` and radius `r`, if the part still has it.

    Everything on a surface of revolution is a circle about the axis, so an
    edge is addressed by the two numbers that define it rather than hunted for.
    """
    found = []
    for edge in shape.val().Edges():
        if edge.geomType() != "CIRCLE":
            continue
        c = edge.Center()
        if abs(c.z - z) < 1e-6 and math.hypot(c.x, c.y) < 1e-6:
            if abs(edge.radius() - r) < 1e-6:
                found.append(edge)
    return found


def largest(shape, edges, *lengths):
    """Break `edges` at the biggest fraction of `lengths` that will build.

    Same retreat as vessel_3_eclipse: a chamfer that will not build at the
    size asked for is worth having at a smaller one, and worth reporting as
    having been shrunk rather than silently dropped.
    """
    if not edges:
        return shape, 0.0
    for f in BREAK_FRACTIONS:
        try:
            return shape.edges(These(edges)).chamfer(*[f * n for n in lengths]), f
        except Exception:
            continue
    return shape, 0.0


def break_edges(shape):
    """Bed-side edges at 30 degrees, everything else symmetric at 45.

    The part prints cylinder-down (see the module docstring), so z=0 is the
    bed. A symmetric 45 degree chamfer there is an overhang from the first
    layer; 30 degrees from vertical leaves margin, the same split the LED Sun
    Lid and both Eclipse lids use.

    The flange's inner underside corner gets a fillet rather than a chamfer.
    It is a reentrant corner carrying the whole weight of the part on the
    glass rim, so the rounded version is both the stronger one and the one
    that ramps the 4mm step instead of printing it as a bare overhang. It is
    kept small: it is taken out of the bearing face, and what is left of that
    face is what actually sits on the rim.
    """
    report = {}

    # z=0, the bed. Both rims of the cylinder.
    bed = ring_edge(shape, 0.0, SEAT_R) + ring_edge(shape, 0.0, SEAT_IR)
    shape, f = largest(shape, bed, BED_BREAK_RUN, BED_BREAK_RISE)
    report["bed"] = (len(bed) if f else 0, f * BED_BREAK_SPAN)

    # The flange's reentrant underside corner.
    seat_step = ring_edge(shape, SEAT_H, SEAT_R)
    try:
        shape = shape.edges(These(seat_step)).fillet(FLANGE_FILLET)
        report["flange"] = (len(seat_step), FLANGE_FILLET)
    except Exception:
        report["flange"] = (0, 0.0)

    # The brim's own top corner, and the hub's top face, both cosmetic.
    brim = ring_edge(shape, SHADE_Z0, BRIM_R)
    shape, f = largest(shape, brim, BRIM_BREAK)
    report["brim"] = (len(brim) if f else 0, f * BRIM_BREAK)

    top = ring_edge(shape, TOP_Z, HUB_OR) + ring_edge(shape, TOP_Z, HUB_IR)
    shape, f = largest(shape, top, TOP_BREAK)
    report["top"] = (len(top) if f else 0, f * TOP_BREAK)

    return shape, report


# --- Assembly --------------------------------------------------------------
def build():
    shade = body()
    shade, breaks = break_edges(shade)
    shade = shade.cut(passthrough_cutter())

    shade = engrave_radial_text(
        shade, f"{2 * SEAT_R:g}", SEAT_R, +1, SEAT_LABEL_Z, theta0=SEAT_LABEL_THETA
    )
    shade = engrave_radial_text(
        shade, f"{HUB_BORE:g}", HUB_IR, -1, HUB_LABEL_Z, theta0=HUB_LABEL_THETA
    )
    return shade, breaks


shade, BREAKS = build()

# Modelled in its seated frame, and printed in it too: the cylinder is already
# on the bed and the hub is already up. Nothing to flip, unlike the Eclipse
# lids -- see the module docstring on which face carries the overhang.
print_shade = shade


# The angle both conical faces stand at, and what it would take to reach 45.
WALL_FROM_VERTICAL = math.degrees(math.atan2(BRIM_R - HUB_OR, SHADE_H))
SHADE_H_FOR_45 = BRIM_R - HUB_OR

# A horizontal wall measured across a face this steep flatters itself. What the
# plastic is actually worth is the thickness through the face -- the horizontal
# figure times the cosine of the angle it leans at.
_LEAN = math.cos(math.radians(WALL_FROM_VERTICAL))
NORMAL_WALL_BRIM = (BRIM_R - SHADE_IR0) * _LEAN
NORMAL_WALL_HUB = (HUB_OR - HUB_IR) * _LEAN

if __name__ == "__main__":
    show_object(
        print_shade,
        name="lamp_shade",
        options={"color": (250, 190, 60), "alpha": 1.0},
        clear=True,
    )

    dx, dy, dz = print_volume.extents(print_shade)
    n = len(shade_points(BRIM_R, HUB_OR)) - 1
    print(f"profile      {SHADE_PROFILE.__name__}, {SHADE_STEPS} samples -> "
          f"{n} segment{'' if n == 1 else 's'}")
    print(f"seat         {2 * SEAT_R:.1f} dia x {SEAT_H:g} deep into the mouth "
          f"({VESSEL_TOP_ID:g} at {MOUTH_FIT:g} allowance), bore {2 * SEAT_IR:.1f}")
    print(f"flange       {2 * BRIM_R:.1f} dia x {FLANGE_H:g}, {FLANGE_REACH:g} "
          f"proud of the seat, beds on the rim at z {SEAT_H:g}")
    print(f"shade        {2 * BRIM_R:.1f} -> {2 * HUB_OR:.1f} dia over {SHADE_H:g}, "
          f"wall {BRIM_R - SHADE_IR0:g} -> {HUB_OR - HUB_IR:g} horizontal, "
          f"{NORMAL_WALL_BRIM:.2f} -> {NORMAL_WALL_HUB:.2f} through the face")
    print(f"hub          bore {HUB_BORE:g} over {RING_OD:.4f} OD, {HUB_H:g} tall; "
          f"lip {LIP_WIDTH:g} reach x {LIP_HEIGHT:g} high, bore {2 * LIP_BORE_R:.1f}")
    print(f"ring light   seats at z {SEAT_Z:.2f}, top at {RING_TOP_Z:.3f}, "
          f"{TOP_Z - RING_TOP_Z:.3f} below the hub top")
    print(f"cable        bend R{BEND_R:.3f} centreline, turns up at y "
          f"{GLAND_END:.2f}, exits the top face "
          f"({HUB_OR - GLAND_END:.2f} of wall left outboard)")
    for name, (n, size) in BREAKS.items():
        print(f"break {name:8s} {n} edge{'' if n == 1 else 's'}, {size:.2f}")
    print(f"overhang     both cone faces {WALL_FROM_VERTICAL:.1f} deg from "
          f"vertical ({90 - WALL_FROM_VERTICAL:.1f} from horizontal)"
          + ("" if WALL_FROM_VERTICAL <= 45.0
             else f"  <-- needs SHADE_H {SHADE_H_FOR_45:.1f} to reach 45"))
    print(f"extent       {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(print_shade.val().Solids())} body, "
          f"{print_shade.val().Volume() / 1000:.1f} cm3")
    print(f"bed          {'fits' if print_volume.fits(print_shade) else 'DOES NOT FIT'}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(print_shade, str(OUTPUT_DIR / "lamp_shade.step"))

    # The drawing is an output of the model, not a thing made by hand once and
    # left to rot: it is regenerated on every run from the same solid that is
    # exported, so it cannot describe a part that no longer exists.
    sheet_path = drawing.sheet(
        print_shade, str(OUTPUT_DIR / "lamp_shade_sheet.svg"), "LAMP SHADE",
        fields=[
            ("PART", "lamp_shade/shade.py"),
            ("VESSEL", f"1  (mouth {VESSEL_TOP_ID:g})"),
            ("LIGHT", f"LED ring 1  (bore {HUB_BORE:g})"),
            ("PROFILE", SHADE_PROFILE.__name__),
            ("ENVELOPE", f"{dx:.1f} x {dy:.1f} x {dz:.1f}"),
            ("VOLUME", f"{print_shade.val().Volume() / 1000:.1f} cm3"),
        ],
    )
    print(f"sheet        {sheet_path}")
