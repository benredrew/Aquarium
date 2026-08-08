# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit bowl -- the inverse of base.py: the cradle the vessel base sits in,
rather than a model of the vessel base itself.

The cradle is one sector of the same cavity profile base.py describes --
cylinder plus bottom corner radius -- grown by CLEARANCE. There is no floor:
the vessel is carried on the curved lip that reaches in under its corner
radius, so no material sits under the middle of the vessel where it would only
add mass.

The vessel is 180mm OD and the bed is 180mm square, so the full cradle ring
(188.2mm OD) does not fit. Two ways out are modelled here:

  `ring_clipped` -- the whole ring with everything outside the build volume
      trimmed off, leaving one connected body with four flats. This is what the
      module exports.
  `segments`     -- the ring cut into ARC_COUNT separate arcs, each printed on
      its own and assembled around the vessel. Kept because it is the stronger
      option; see the note on ring_clipped's webs below.

Reuses base.py's confirmed OD/height/corner-radius (rather than restating them)
so the two shapes cannot drift apart as either is refined.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import print_volume
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"


def load_part(relative_path, name):
    """Import base.py for its geometry/dimensions only (no viewer/export)."""
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_mod = load_part("base.py", "base")

# --- Print constraints ----------------------------------------------------
# Build volume lives in ../print_volume.py; see it in the preview.
EXTRUSION_WIDTH = 0.45  # 0.4mm nozzle, 0.20mm STRUCTURAL profile

# --- Design parameters ----------------------------------------------------
# Standard free fit on a vertical wall: 0.2mm radial, so a bore comes out 0.4mm
# over the shaft it takes. Same figure the lid and screen mate on
# (lid.SCREEN_CLEARANCE), and the convention is recorded in ../DIMENSIONS.md.
CLEARANCE = 0.2
# Wall is a whole number of extrusion widths (8), so it prints as solid
# perimeters with no sliver of infill trapped in the middle.
WALL = 8 * EXTRUSION_WIDTH  # 3.60
# Tall enough to stand up past the corner radius onto the straight wall, which
# is what stops the vessel rocking; the grip itself is the lip below.
GRIP_HEIGHT = 12.0
# The vessel is lifted clear of the bed by this much, so the seat has material
# under it rather than running out to a feather edge at z=0. The floor is only
# generated outboard of the tangent ring, where the corner radius meets the flat
# bottom -- inboard of that it would carry nothing, so the middle is left open
# and the part comes out a donut.
FLOOR = 2.0
ARC_COUNT = 4  # segments, for the `segments` alternative
ARC_ANGLE = 60.0  # degrees of vessel circumference each segment grips

CAVITY_R = base_mod.OD / 2 + CLEARANCE  # 90.50
CAVITY_CORNER_RADIUS = base_mod.CORNER_RADIUS + CLEARANCE  # 5.50
OUTER_R = CAVITY_R + WALL  # 94.10
# Innermost reach of the lip, where it tucks under the vessel's corner radius.
LIP_R = CAVITY_R - CAVITY_CORNER_RADIUS  # 85.00

# Labels sit on the straight band of outer wall above the corner radius, and on
# the diagonals -- where the build volume clips nothing away. On axis the outer
# wall is trimmed off and the text would go with it.
#
# Two of them: the tank OD the cradle was cut for, and the cradle's own OD. The
# tank figure is the one that matters when checking a print against the glass;
# the cradle figure is nominal, since the plate flattens it on the four axes.
LABEL_Z = (CAVITY_CORNER_RADIUS + GRIP_HEIGHT) / 2
LABELS = (
    (f"TANK {base_mod.OD:g}", math.pi / 4),
    (f"ID {2 * CAVITY_R:g}", 3 * math.pi / 4),
    (f"CRADLE {2 * OUTER_R:g}", 5 * math.pi / 4),
)


def sector(angle_deg, radius, height, rotation_deg):
    """A pie-slice solid, centred on `rotation_deg`, for trimming the ring.

    The outer arc is built through an explicit midpoint rather than with
    radiusArc: radiusArc's sign convention bowed the arc inward, toward the
    origin, which trimmed away the middle of every segment and left two thin
    slivers at the sector edges. threePointArc has no sign to get wrong.
    """
    half = math.radians(angle_deg / 2)
    start = (radius * math.cos(-half), radius * math.sin(-half))
    mid = (radius, 0.0)
    end = (radius * math.cos(half), radius * math.sin(half))
    return (
        cq.Workplane("XY")
        .moveTo(0, 0)
        .lineTo(*start)
        .threePointArc(mid, end)
        .close()
        .extrude(height)
        .rotate((0, 0, 0), (0, 0, 1), rotation_deg)
    )


# --- Constant stiffness round the circumference ---------------------------
# The build plate clips the ring on the four axes, so the wall there runs out to
# almost nothing while the diagonals keep the full section. Left alone those
# flats are the floppy bits.
#
# The stiffness being held constant is the second moment of area of the radial
# section about an axis NORMAL to that section -- running circumferentially --
# through the centre of curvature of the seat fillet. That is the point the
# section pivots about when the ring tries to roll: the wall tips out, the floor
# lifts, and the fillet stays put. Being a polar moment about a fixed point, and
# not a bending moment about the section's own centroid, it rewards material
# placed far from that point in any direction.
#
# Which is why the floor is what varies. Pulling its inner edge inward puts
# material a long way from the fillet centre radially, where it counts several
# times more per unit area than the same material added out at the wall.
FILLET_CENTRE_R = LIP_R  # 84.50 -- where the seat's arc is struck from
FILLET_CENTRE_Z = FLOOR + CAVITY_CORNER_RADIUS  # 7.20

HEIGHT = FLOOR + GRIP_HEIGHT  # uniform; the floor does the compensating
SECTION_STEPS = 2000  # integration steps across the fillet-and-wall part
FLOOR_INNER_MIN = 20.0  # how far in the floor may ever reach
# Wall thinner than this cannot be printed -- it is under one extrusion width --
# so it is not generated at all. Those sectors keep the seat and the floor and
# stop at the bore.
MIN_WALL = 0.6
EDGE_ROUND = 0.3  # radius on every Z-parallel corner


def clip_radius(theta):
    """How far the build plate lets the ring reach at this angle."""
    reach = max(abs(math.cos(theta)), abs(math.sin(theta)))
    return min(OUTER_R, (print_volume.BED_X / 2) / reach)


def wall_top(theta):
    """How high the wall stands at this angle.

    The wall is two things stacked, and only the upper one is ever dropped.

    Below the seat's tangent -- z under FILLET_CENTRE_Z -- the material backs
    the corner radius. Its thickness is set by where the seat's arc has got to
    at that height, not by the bore, so it stays substantial right out to the
    plate and is always worth keeping.

    Above the tangent the wall is the plain vertical band between bore and
    plate, and its thickness is exactly what the plate leaves. Where that comes
    out under MIN_WALL it cannot be printed, so it is not generated: the wall
    stops at the tangent and the seat carries on alone.
    """
    r_out = clip_radius(theta)
    return HEIGHT if r_out - CAVITY_R >= MIN_WALL else FILLET_CENTRE_Z


# Half-width of the sectors whose wall is too thin to print, about each axis.
THIN_WALL_HALF_ANGLE = (
    math.degrees(math.acos(min((print_volume.BED_X / 2) / (CAVITY_R + MIN_WALL), 1.0)))
    if CAVITY_R + MIN_WALL > print_volume.BED_X / 2
    else 0.0
)


def section_top(r, top):
    """Height of the section's top face at radius `r`, given the wall's height.

    Not a pair of rectangles: between the tangent ring and the bore the top face
    is the seat fillet itself, climbing from FLOOR to FLOOR + the corner radius.
    The arc is evaluated exactly at every sample, never chorded.
    """
    if r < LIP_R:
        return FLOOR
    if r <= CAVITY_R:
        return (
            FLOOR
            + CAVITY_CORNER_RADIUS
            - math.sqrt(max(CAVITY_CORNER_RADIUS**2 - (r - LIP_R) ** 2, 0.0))
        )
    return top


# Contribution of a unit height of floor, per mm of radius, to the moment. The
# floor sits at a constant FLOOR high, so its whole contribution integrates in
# closed form -- see floor_width_for.
_FLOOR_COLUMN = ((FLOOR - FILLET_CENTRE_Z) ** 3 + FILLET_CENTRE_Z**3) / 3.0


def outboard_moment(r_out, top):
    """Moment of everything from the tangent ring outward, about the fillet centre.

    Integrates (r - Rc)^2 + (z - Zc)^2 over the section. The z part is closed
    form up the column at each radius, so only the radial sweep is stepped, and
    the seat's arc is sampled exactly rather than approximated by segments.
    """
    step = (r_out - LIP_R) / SECTION_STEPS
    total = 0.0
    for i in range(SECTION_STEPS):
        r = LIP_R + (i + 0.5) * step
        height = section_top(r, top)
        total += (
            (r - FILLET_CENTRE_R) ** 2 * height
            + ((height - FILLET_CENTRE_Z) ** 3 + FILLET_CENTRE_Z**3) / 3.0
        ) * step
    return total


# The diagonal section, which the plate never touches, sets the target. Its
# floor stops at the tangent ring, so that is the leanest the floor ever gets.
TARGET_IP = outboard_moment(OUTER_R, HEIGHT)


def floor_width_for(deficit):
    """Floor width inboard of the tangent ring that supplies `deficit`.

    Solved rather than searched. Inboard of the tangent ring the floor is a
    constant FLOOR high, and the moment axis passes through the tangent ring's
    own radius, so the contribution of a floor w wide is exactly

        (FLOOR / 3) w^3  +  _FLOOR_COLUMN w

    -- a cubic in w, monotonic, inverted here by Newton from the linear guess.
    No bisection, and no integration error in the part that is being solved for.
    """
    if deficit <= 0:
        return 0.0
    w = deficit / _FLOOR_COLUMN  # exact when the cubic term is still small
    for _ in range(40):
        f = FLOOR / 3 * w**3 + _FLOOR_COLUMN * w - deficit
        df = FLOOR * w**2 + _FLOOR_COLUMN
        step = f / df
        w -= step
        if abs(step) < 1e-12:
            break
    return w


def floor_edge(theta):
    """Inner edge of the floor at this angle, solved exactly.

    Note the section keeps its full radial reach even where the wall has been
    dropped -- the plate still bounds the seat's backing below the tangent. Only
    the height above the tangent changes.
    """
    deficit = TARGET_IP - outboard_moment(clip_radius(theta), wall_top(theta))
    return max(LIP_R - floor_width_for(deficit), FLOOR_INNER_MIN)


# Angles the floor cannot reach far enough inward to rescue. Empty is healthy.
SHORTFALL_ANGLES = [
    a for a in range(0, 91) if floor_edge(math.radians(a)) <= FLOOR_INNER_MIN + 1e-9
]


def floor_hole_cutter(steps=720):
    """The opening in the floor -- a lobed prism, not a cylinder.

    Its radius is floor_edge(theta), reaching furthest inward on the four axes
    where the plate has taken most from the wall, and relaxing back to the
    tangent ring on the diagonals.

    A polyline, deliberately. Drawing it as a spline through the same points
    looked tidier and was wrong twice over: the curve came out well inside the
    points it was given -- a cutter of 30695mm^3 against the 40837mm^3 the
    polygon measures -- and the solid it made turned every subsequent boolean
    into an empty result. At `steps` segments the chord error is under 0.002mm,
    a fiftieth of a layer, and the facet corners sit far enough inboard that the
    corner-rounding pass filters them out by radius.
    """
    points = []
    for i in range(steps):
        theta = 2 * math.pi * i / steps
        r = floor_edge(theta)
        points.append((r * math.cos(theta), r * math.sin(theta)))
    return cq.Workplane("XY").polyline(points).close().extrude(FLOOR)


def thin_wall_cutters():
    """The vertical wall in the sectors where it comes out under MIN_WALL thick.

    Reaches down only as far as the seat's tangent, never below it. The backing
    under the seat is a different piece of wall -- thicker, and not what the
    plate has thinned -- and it stays.

    Stopping at the tangent also keeps the rounding pass working. Cutting the
    full height put a corner on the bore running from the floor up to the
    tangent seam between the seat's torus and the bore cylinder, and a fillet
    cannot terminate on a tangency: eight of those refused at every radius down
    to 0.02, and moving the cut to dodge the tangency segfaulted OCC. Cut above
    the tangent and the corner starts there instead, where it blends cleanly.
    """
    if THIN_WALL_HALF_ANGLE <= 0:
        return []

    height = HEIGHT + 2 - FILLET_CENTRE_Z
    bore = (
        cq.Workplane("XY")
        .circle(CAVITY_R)
        .extrude(height)
        .translate((0, 0, FILLET_CENTRE_Z))
    )
    return [
        sector(2 * THIN_WALL_HALF_ANGLE, OUTER_R + 5, height, axis)
        .translate((0, 0, FILLET_CENTRE_Z))
        .cut(bore)
        for axis in (0.0, 90.0, 180.0, 270.0)
    ]


def round_vertical_corners(shape, radius):
    """Round every Z-parallel corner on the wall to `radius`.

    Two things have to be kept out of the selection.

    A closed cylinder carries a seam edge running parallel to Z that looks just
    like a corner to a direction filter; rounding it would cut a groove down an
    otherwise smooth bore. Every genuine corner here is made by a plane meeting
    something -- a build-plate flat, or the radial face of a dropped wall sector
    -- so an edge only qualifies if a planar face meets along it, which the seam
    on a bore never does.

    And the floor's opening is excluded by radius. It is a spline, smooth by
    construction, so it has no corners to round; anything found down there would
    be an artefact.
    """
    solid = shape.val()

    on_a_plane = [
        edge.wrapped
        for face in solid.Faces()
        if face.geomType() == "PLANE"
        for edge in face.Edges()
    ]

    keep = []
    for edge in shape.edges("|Z").vals():
        centre = edge.Center()
        if math.hypot(centre.x, centre.y) < CAVITY_R - 0.5:
            continue
        if any(edge.wrapped.IsSame(other) for other in on_a_plane):
            keep.append(edge)

    if not keep:
        return shape, []

    def blend(edges):
        builder = BRepFilletAPI_MakeFillet(solid.wrapped)
        for edge in edges:
            builder.Add(radius, TopoDS.Edge_s(edge.wrapped))
        builder.Build()
        return cq.Shape.cast(builder.Shape())

    try:
        return cq.Workplane(obj=blend(keep)), []
    except Exception:
        pass

    # Something in the set will not blend. Find which, rather than dropping the
    # whole pass: the corners where a dropped wall sector meets the bore run
    # from the floor up to the tangent seam between the seat's torus and the
    # bore cylinder, and a fillet cannot terminate on a tangency. Those refuse
    # at every radius tried, down to 0.02. Nudging the cut off the tangency to
    # avoid it segfaults OCC outright, so they are left sharp and reported.
    good, skipped = [], []
    for edge in keep:
        try:
            blend([edge])
            good.append(edge)
        except Exception:
            centre = edge.Center()
            skipped.append(
                (
                    round(math.degrees(math.atan2(centre.y, centre.x)) % 360, 2),
                    round(edge.Length(), 3),
                )
            )
    if not good:
        return shape, skipped
    return cq.Workplane(obj=blend(good)), skipped


def build_ring():
    """The full cradle ring, wider than the bed until it is clipped.

    Prints as-is with the z=0 face on the bed and needs no supports: nothing
    overhangs, since the seat only ever curves inward going up.
    """
    ring = cq.Workplane("XY").circle(OUTER_R).extrude(HEIGHT)

    # The vessel's own shape, stood on the floor -- cylinder plus the corner
    # radius -- swept up and out through the top.
    cavity = cq.Workplane("XY").circle(CAVITY_R).extrude(HEIGHT + 1)
    cavity = cavity.faces("<Z").edges().fillet(CAVITY_CORNER_RADIUS)
    ring = ring.cut(cavity.translate((0, 0, FLOOR)))

    # Open the middle out. The floor keeps only what it needs: back at the
    # tangent ring on the diagonals, reaching further inward on the four axes to
    # make up what the plate took off the wall there.
    ring = ring.cut(floor_hole_cutter())

    return ring


ring = build_ring()

# What survives inside the build volume: the ring with four flats milled off
# where it overran the bed, still one connected body.
ring_clipped = ring.intersect(print_volume.volume)

# Drop the wall wherever the flats would leave it too thin to print.
for cutter in thin_wall_cutters():
    ring_clipped = ring_clipped.cut(cutter)

# Round the corners before the labels go on. Engraved text is full of Z-parallel
# edges of its own, and the rounding pass would happily find every one of them.
ring_clipped, UNROUNDED_CORNERS = round_vertical_corners(ring_clipped, EDGE_ROUND)

for _text, _theta in LABELS:
    ring_clipped = engrave_radial_text(
        ring_clipped, _text, OUTER_R, +1, FLOOR + LABEL_Z, theta0=_theta
    )

# The earlier alternative: four separate arcs, each well inside the bed.
segments = [
    ring.intersect(sector(ARC_ANGLE, OUTER_R + 5, HEIGHT, 360.0 * i / ARC_COUNT))
    for i in range(ARC_COUNT)
]

if __name__ == "__main__":
    show_object(base_mod.base, name="vessel_base", clear=True)
    show_object(ring_clipped, name="bowl_ring_clipped")
    print_volume.show(show_object)

    dx, dy, dz = print_volume.extents(ring_clipped)
    print(f"clipped ring: {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(ring_clipped.val().Solids())} body, "
          f"{ring_clipped.val().Volume() / 1000:.1f} cm3")
    if print_volume.fits(ring_clipped):
        cq.exporters.export(ring_clipped, str(OUTPUT_DIR / "bowl_ring.step"))
    else:
        print(
            f"NOT exported: does not fit the "
            f"{print_volume.BED_X:g}x{print_volume.BED_Y:g}x{print_volume.BED_Z:g} "
            f"build volume."
        )
