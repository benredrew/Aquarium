# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Test-fit bowl -- the inverse of base.py: the cradle the vessel base sits in,
rather than a model of the vessel base itself.

The cradle is one sector of the same cavity profile base.py describes --
cylinder plus bottom corner radius -- grown by CLEARANCE. There is no floor:
the vessel is carried on the curved lip that reaches in under its corner
radius, so no material sits under the middle of the vessel where it would only
add mass.

The vessel is 178mm OD and the bed is 180mm square, so the full cradle ring
(185.6mm OD) does not fit. Two ways out are modelled here:

  `ring_clipped` -- the whole ring with everything outside the build volume
      trimmed off, leaving one connected body with four flats. This is what the
      module exports.
  `segments`     -- the ring cut into ARC_COUNT separate arcs, each printed on
      its own and assembled around the vessel. Kept because it is the stronger
      option; see the note on ring_clipped's webs below.

Reuses base.py's OD/height/corner-radius rather than restating them, so the two
shapes cannot drift apart as either is refined. base.py in turn reads the vessel
figures from ../spec/vessel.md, so the chain runs document -> vessel -> cradle
and the diameter is edited in one place. CLEARANCE comes from ../spec/fits.md
the same way. Both base figures were confirmed by this cradle printed 2026-08-08
-- cut for 178 with the 0.4mm diametral free fit, and it fitted perfectly.

Revision, 2026-08-08: the 2mm floor is gone, and the constant-stiffness scheme
it carried went with it, to get a prototype off the printer sooner. That scheme
varied the floor's inner edge with angle so every radial section held the same
second moment about the seat fillet's centre of curvature, making up on the four
axes what the build plate takes off the wall there. It is worth having back --
the working is in the git history, not reconstructed from scratch. Note the cost
of the regression: with no floor under it the seat's inner lip is tangent to
z=0, so it runs out to a feather edge at LIP_R.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import print_volume
import specs
from engrave import engrave_radial_text
from cadkit.viewer import show as show_object
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS

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
# (lid.SCREEN_CLEARANCE); both read it from ../spec/fits.md.
CLEARANCE = specs.figure("fits", "free_wall_radial")
# Wall is a whole number of extrusion widths (8), so it prints as solid
# perimeters with no sliver of infill trapped in the middle.
WALL = 8 * EXTRUSION_WIDTH  # 3.60
# Tall enough to stand up past the corner radius onto the straight wall, which
# is what stops the vessel rocking; the grip itself is the lip below.
GRIP_HEIGHT = 12.0
ARC_COUNT = 4  # segments, for the `segments` alternative
ARC_ANGLE = 60.0  # degrees of vessel circumference each segment grips

CAVITY_R = base_mod.OD / 2 + CLEARANCE  # 89.20
CAVITY_CORNER_RADIUS = base_mod.CORNER_RADIUS + CLEARANCE  # 5.20
OUTER_R = CAVITY_R + WALL  # 92.80
# Innermost reach of the lip, where it tucks under the vessel's corner radius.
LIP_R = CAVITY_R - CAVITY_CORNER_RADIUS  # 84.00

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


# --- Heights and printability --------------------------------------------
# Where the seat's arc is tangent to the bore, i.e. the top of the curved lip
# and the bottom of the plain vertical wall. The wall is two things stacked
# either side of this height, and only the upper one is ever dropped.
SEAT_TANGENT_Z = CAVITY_CORNER_RADIUS  # 5.20

HEIGHT = GRIP_HEIGHT  # uniform; nothing under the seat now to add to it
# Wall thinner than this cannot be printed -- it is under one extrusion width --
# so it is not generated at all. Those sectors keep the seat and stop at the
# bore. Below the tangent the material backs the corner radius and its thickness
# comes from the seat's arc rather than the bore, so it always stays.
MIN_WALL = 0.6
EDGE_ROUND = 0.3  # radius on every Z-parallel corner

# Half-width of the sectors whose wall is too thin to print, about each axis.
THIN_WALL_HALF_ANGLE = (
    math.degrees(math.acos(min((print_volume.BED_X / 2) / (CAVITY_R + MIN_WALL), 1.0)))
    if CAVITY_R + MIN_WALL > print_volume.BED_X / 2
    else 0.0
)


def thin_wall_cutters():
    """The vertical wall in the sectors where it comes out under MIN_WALL thick.

    Reaches down only as far as the seat's tangent, never below it. The backing
    under the seat is a different piece of wall -- thicker, and not what the
    plate has thinned -- and it stays.

    Stopping at the tangent also keeps the rounding pass working. Cutting the
    full height put a corner on the bore running from z=0 up to the
    tangent seam between the seat's torus and the bore cylinder, and a fillet
    cannot terminate on a tangency: eight of those refused at every radius down
    to 0.02, and moving the cut to dodge the tangency segfaulted OCC. Cut above
    the tangent and the corner starts there instead, where it blends cleanly.
    """
    if THIN_WALL_HALF_ANGLE <= 0:
        return []

    height = HEIGHT + 2 - SEAT_TANGENT_Z
    bore = (
        cq.Workplane("XY")
        .circle(CAVITY_R)
        .extrude(height)
        .translate((0, 0, SEAT_TANGENT_Z))
    )
    return [
        sector(2 * THIN_WALL_HALF_ANGLE, OUTER_R + 5, height, axis)
        .translate((0, 0, SEAT_TANGENT_Z))
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

    And anything inboard of the bore is excluded by radius. Nothing down there
    has a corner to round -- the seat is a surface of revolution -- so an edge
    found there would be an artefact.
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
    # from z=0 up to the tangent seam between the seat's torus and the
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

    # The vessel's own shape, stood on the bed -- cylinder plus the corner
    # radius -- swept up and out through the top. With no floor under it this
    # cut opens the middle by itself: at z=0 it reaches out to LIP_R, so what
    # is left is a donut, and the seat is all that touches the vessel.
    cavity = cq.Workplane("XY").circle(CAVITY_R).extrude(HEIGHT + 1)
    cavity = cavity.faces("<Z").edges().fillet(CAVITY_CORNER_RADIUS)
    ring = ring.cut(cavity)

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
        ring_clipped, _text, OUTER_R, +1, LABEL_Z, theta0=_theta
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
