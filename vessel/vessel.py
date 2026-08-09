# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Reference model of the vessel, measured off a silhouette.

The vessel's **exterior envelope**, as a solid of revolution. A silhouette
carries nothing about wall thickness, so none is modelled. This exists to design
parts around: what the cradle grips, what the lid sits in, what clears what.

## Source

`aquarium.png` -- the tank isolated on white. The whole cut-out is vessel: where
it meets white *is* the vessel's edge, brim and base included. There is no lid
and no tray to trim off, and trimming for them (an earlier mistake here) throws
away 12mm of real height at the top and cuts the base off at a chord.

## The ends are circles, so they project as ellipses

Seen from a camera raised by theta, a circle on the axis projects to an ellipse:
major axis 2r across, unchanged; minor axis 2r*sin(theta). Each end arc gives
three things at once --

    major axis  ->  the true diameter of that circle
    b / a       ->  sin(theta), the camera elevation
    tangent row ->  the true height of that circle's plane

-- so an end must never be read as a straight chord across the outline. A chord
is neither the diameter nor at the right height, and it was reading the base as
a chord that made the first attempt at this too short.

The base arc is whole and measures a=579.5px, b=79.0px, giving **7.84 degrees**.
The brim's arc runs off the top of the frame, so its apex is missing and only a
lower bound survives -- but that bound is the check: 7.84 degrees predicts a
brim minor axis of 80.6px, which places its apex 22px above the frame edge,
exactly as observed. The two ends agree.

Between the two tangent planes the outline is formed at tangent points, so
half-widths there are true radii at true heights. Heights are divided by
cos(7.84 deg) to undo the foreshortening; radii need no such correction.

## Scale

One anchor: the base ellipse's **major axis** is the vessel OD from
../spec/vessel.md -- the figure the printed cradle confirmed by fitting. That
fixes 6.51 px/mm, and every other dimension here is that ratio on the outline.
All of them are derived; none is measured; none belongs in the spec document
until a caliper or a printed part says so.

## What is still open

The raw phone photo (IMG_6356) reads the body about 4.5% wider than this. The
two agree on the waist to 0.3%, which is reassuring, but they do not agree on
the body, and this image is the one that has been through an image model. A
caliper across the body would settle it. Treat diameters as +/-2% meanwhile.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import engrave
import specs
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

VESSEL_OD = specs.figure("vessel", "base_od")

# --- The stack ------------------------------------------------------------
# Five outer diameters, top to bottom: rim, waist, body, waist, bottom. Every
# figure here is on a 0.1mm grid -- the measurement does not support more, and
# carrying two decimals implied a precision the photograph cannot give.
#
# The two waists are one feature used twice: identical metal bands wrapped both
# before this jar was repurposed, so they are the same diameter and the same
# height, and that is a statement about the object rather than a reading of the
# picture. The outline disagrees -- it shows the lower waist about 5mm shorter
# -- and the outline is what loses. The substrate line sits across that waist in
# the photograph, which is the likely reason it reads short.
RIM_DIA = 181.4
WAIST_DIA = 165.7
BODY_DIA = 178.8
BULGE_DIA = 178.0          # the vessel OD, the one anchored figure
WAIST_WALL = 15.4          # straight wall of each waist -- what a band wraps

# The bottom has no flat wall. The R8 roll rises to its crest at BULGE_DIA with
# a vertical tangent, and the neck out of it leaves on that same tangent -- the
# two radii meet, and the crest is a point, not a band. Giving it a straight
# wall put a corner on the bulge that the glass does not have.
BULGE_CREST = 8.0          # = CORNER_R: where the roll goes vertical
NECK = 12.4                # crest to the waist wall, all curve

BLEND_WAIST_BODY = 10.2    # both waist/body junctions -- same feature twice
BLEND_WAIST_RIM = 6.2

RIM_TOP = 156.4
UPPER_WAIST_TOP = 144.4    # measured, and taken as truth

# Built downward from the rim, then upward from the crest; the body absorbs
# whatever is left between them, which is the only section with slack in it.
_uw_wall_hi = UPPER_WAIST_TOP - BLEND_WAIST_RIM / 2
_uw_wall_lo = _uw_wall_hi - WAIST_WALL
_lw_wall_lo = BULGE_CREST + NECK
_lw_wall_hi = _lw_wall_lo + WAIST_WALL

SECTIONS = (
    #  name           diameter    z from                       z to
    ("bottom",        BULGE_DIA,  BULGE_CREST,                 BULGE_CREST + NECK / 2),
    ("waist, lower",  WAIST_DIA,  BULGE_CREST + NECK / 2,      _lw_wall_hi + BLEND_WAIST_BODY / 2),
    ("body",          BODY_DIA,   _lw_wall_hi + BLEND_WAIST_BODY / 2, _uw_wall_lo - BLEND_WAIST_BODY / 2),
    ("waist, upper",  WAIST_DIA,  _uw_wall_lo - BLEND_WAIST_BODY / 2, UPPER_WAIST_TOP),
    ("rim",           RIM_DIA,    UPPER_WAIST_TOP,             RIM_TOP),
)

TRANSITIONS = {
    SECTIONS[0][3]: NECK,
    SECTIONS[1][3]: BLEND_WAIST_BODY,
    SECTIONS[2][3]: BLEND_WAIST_BODY,
    SECTIONS[3][3]: BLEND_WAIST_RIM,
}

CORNER_R = specs.figure("vessel", "base_corner_radius")   # 8, settled on glass
HEIGHT = SECTIONS[-1][3]
FLAT_DIA = SECTIONS[0][1] - 2 * CORNER_R      # what it actually stands on


def _blend(r1, r2, zj, T):
    """Two tangent arcs joining vertical walls r1 (below) and r2 (above).

    Each arc turns through alpha, meeting at the inflection halfway. Solving
    the pair for a given radial step d and transition height T gives

        alpha = 2*atan(d / T),      radius = T / (2*sin(alpha))

    so the blend spans exactly T in z and lands tangent to both walls. Returned
    as (through, end) pairs for threePointArc, which has no sign convention to
    get wrong -- radiusArc does, and it bows the wrong way about half the time.
    """
    d = r1 - r2
    if abs(d) < 1e-9:
        return []
    alpha = 2 * math.atan(abs(d) / T)
    rad = T / (2 * math.sin(alpha))
    sgn = 1.0 if d > 0 else -1.0
    rm, z0 = (r1 + r2) / 2, zj - T / 2
    c1 = (r1 - sgn * rad, z0)
    mid1 = (c1[0] + sgn * rad * math.cos(alpha / 2), c1[1] + rad * math.sin(alpha / 2))
    c2 = (r2 + sgn * rad, zj + T / 2)
    mid2 = (c2[0] - sgn * rad * math.cos(alpha / 2), c2[1] - rad * math.sin(alpha / 2))
    return [(mid1, (rm, zj)), (mid2, (r2, zj + T / 2))]


def build_vessel():
    """Revolve the stack: an 8mm roll, five straight walls, blended junctions."""
    wire = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(FLAT_DIA / 2, 0)
        .radiusArc((SECTIONS[0][1] / 2, CORNER_R), -CORNER_R)
    )
    for i, (_, dia, _z0, z1) in enumerate(SECTIONS):
        r = dia / 2
        if i + 1 < len(SECTIONS):
            T = TRANSITIONS[z1]
            # The bottom section has no straight wall at all -- the blend leaves
            # the crest of the roll the moment it arrives -- so this run can be
            # zero-length, and emitting it fails the revolve with a bare
            # "BRepAdaptor_Curve::No geometry".
            if abs((z1 - T / 2) - _z0) > 1e-9:
                wire = wire.lineTo(r, z1 - T / 2)
            for through, end in _blend(r, SECTIONS[i + 1][1] / 2, z1, T):
                wire = wire.threePointArc(through, end)
        else:
            wire = wire.lineTo(r, z1)
    return wire.lineTo(0, HEIGHT).close().revolve(360, (0, 0, 0), (0, 1, 0))


# --- Labels ---------------------------------------------------------------
# Each zone carries its own diameter, on its own wall, all on one vertical line
# so the stack reads top to bottom in a single glance. Engraved rather than
# raised, for the same reason every other interface figure in this project is:
# a raised boss adds to the diameter it claims to describe.
LABEL_ANGLE = 0.0        # +X, and every label shares it

# Inked height of a digit at the shared font size, measured rather than assumed.
LABEL_HEIGHT = (
    cq.Workplane("XY")
    .text("8", engrave.FONT_SIZE, 1.0, combine=False, kind="bold")
    .val().BoundingBox().ylen
)


def wall_span(i):
    """The straight part of section `i` -- what is left between its blends."""
    _, _, z0, z1 = SECTIONS[i]
    lo = z0 + (TRANSITIONS[z0] / 2 if z0 in TRANSITIONS else 0.0)
    hi = z1 - (TRANSITIONS[z1] / 2 if z1 in TRANSITIONS else 0.0)
    return lo, hi


def label_vessel(shape):
    """Engrave each zone's diameter on that zone, centred on its straight wall."""
    for i, (name, dia, _z0, _z1) in enumerate(SECTIONS):
        lo, hi = wall_span(i)
        if hi - lo >= LABEL_HEIGHT:
            z = (lo + hi) / 2
        else:
            # The bulge has no straight wall -- its crest is a tangent point,
            # not a band. The label still goes there: across the text's height
            # the surface falls away by only ~0.2mm, so the ends cut shallow
            # rather than not at all.
            z = _z0
        shape = engrave_radial_text(
            shape, f"{dia:.1f}", dia / 2, +1, z, theta0=LABEL_ANGLE
        )
    return shape


vessel = label_vessel(build_vessel())

if __name__ == "__main__":
    show_object(vessel, name="vessel",
                options={"color": (150, 205, 225), "alpha": 0.55}, clear=True)
    print(f"anchored on vessel OD    {VESSEL_OD:.1f} mm")
    print(f"height, contact to rim   {HEIGHT:.2f} mm")
    print(f"flat bottom              {FLAT_DIA:.2f} mm, rolling on R{CORNER_R:g}")
    print()
    for name, dia, z0, z1 in reversed(SECTIONS):
        print(f"  {name:14s} {dia:7.2f} mm   z {z0:6.2f} .. {z1:6.2f}"
              f"   ({z1 - z0:5.2f} tall)")
    print()
    print()
    print("straight wall of each section (what a label or a band sits on):")
    for i, (name, dia, _z0, _z1) in enumerate(SECTIONS):
        lo, hi = wall_span(i)
        print(f"  {name:14s} {lo:6.2f} .. {hi:6.2f}   ({hi - lo:5.2f} wide)")
    lw = wall_span(1); uw = wall_span(3)
    same = abs((lw[1] - lw[0]) - (uw[1] - uw[0])) < 0.05
    verdict = "identical" if same else "NOT identical"
    print(f"\nwaists: {WAIST_DIA:.1f} dia both, walls "
          f"{lw[1] - lw[0]:.1f} and {uw[1] - uw[0]:.1f} -- {verdict}")
    print(f"exterior envelope        {vessel.val().Volume() / 1e6:.3f} L "
          f"(not capacity)")
    cq.exporters.export(vessel, str(OUTPUT_DIR / "vessel.step"))
    print("  wrote vessel.step")
