# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Shared label engraving for cylindrical interface surfaces.

Interface diameters are engraved (cut in), never raised -- a raised boss would
add to the effective OD and subtract from the effective ID, corrupting the very
fit the labelled diameter controls. This applies to finished parts exactly as
it does to the test-fit jigs.

Text legibility with a 0.4mm nozzle: bold strokes need to print at least
~2 perimeters (~0.8mm) wide, which for a bold sans font needs a cap height of
roughly 5mm. ENGRAVE_DEPTH must stay well under the part's wall thickness.
"""
import math

import cadquery as cq

FONT_SIZE = 5.0
ENGRAVE_DEPTH = 0.3
OVERSHOOT = 0.3  # cutter start outside the wall, avoids coplanar-face booleans
WIDTH_SCALE = 2.0  # stretch text 200% in the circumferential (width) direction
TRACKING = 0.6  # extra gap between character cells, in mm of arc
NARROW_CHARS = ".,'"  # keep their own width rather than a full digit cell


def _glyph_width(ch):
    """Unscaled inked width of a single character at FONT_SIZE."""
    glyph = cq.Workplane("XY").text(
        ch, FONT_SIZE, 1.0, combine=False, kind="bold"
    ).val()
    return glyph.BoundingBox().xlen


def engrave_radial_text(base, txt, radius, direction, z, theta0):
    """Engrave `txt` into a cylindrical wall at the given radius and angle.

    direction: +1 for the outer wall (OD), -1 for the inner wall (ID).
    theta0: angle (radians) around the axis where the text is centered.

    Each character sits on its own tangent plane so the flat cut tracks the
    curved wall closely -- engraving the whole string off one plane would leave
    the outer characters barely scratched as the arc falls away from it.
    """
    # Digits get a uniform (tabular) cell so they stay evenly spaced whatever
    # the glyph. Punctuation keeps its own narrower width, so a decimal point
    # does not sit marooned in a digit-sized gap.
    cell = max(_glyph_width(c) for c in txt if not c.isspace())
    advances = [
        (_glyph_width(ch) if ch in NARROW_CHARS else cell) * WIDTH_SCALE + TRACKING
        for ch in txt
    ]

    cutters = []
    offset = -sum(advances) / 2

    for ch, advance in zip(txt, advances):
        centre = offset + advance / 2
        offset += advance
        if ch.isspace():
            continue
        # Reading direction follows the plane's xDir, which runs with +theta on
        # the outer wall and with -theta on the inner wall.
        theta = theta0 + direction * centre / radius

        origin = cq.Vector(radius * math.cos(theta), radius * math.sin(theta), z)
        normal = cq.Vector(direction * math.cos(theta), direction * math.sin(theta), 0)
        # xDir = Z x normal, so the derived yDir (normal x xDir) is always +Z and
        # the text stays upright regardless of theta or which wall it sits on.
        xDir = cq.Vector(-normal.y, normal.x, 0)

        plane = cq.Plane(origin=origin, normal=normal, xDir=xDir)
        shape = (
            cq.Workplane(plane)
            .workplane(offset=-ENGRAVE_DEPTH)
            .text(
                ch,
                FONT_SIZE,
                ENGRAVE_DEPTH + OVERSHOOT,
                combine=False,
                kind="bold",
                halign="center",
                valign="center",
            )
            .val()
        )

        if WIDTH_SCALE != 1.0:
            # Non-uniform scale along the plane's local width axis (xDir) only,
            # about the plane's origin, leaving height (yDir) and cut depth
            # (normal) unchanged.
            x = plane.xDir
            s = WIDTH_SCALE - 1.0
            m00, m01, m02 = 1 + s * x.x * x.x, s * x.x * x.y, s * x.x * x.z
            m10, m11, m12 = s * x.y * x.x, 1 + s * x.y * x.y, s * x.y * x.z
            m20, m21, m22 = s * x.z * x.x, s * x.z * x.y, 1 + s * x.z * x.z
            tx = origin.x - (m00 * origin.x + m01 * origin.y + m02 * origin.z)
            ty = origin.y - (m10 * origin.x + m11 * origin.y + m12 * origin.z)
            tz = origin.z - (m20 * origin.x + m21 * origin.y + m22 * origin.z)
            shape = shape.transformGeometry(
                cq.Matrix(
                    [
                        [m00, m01, m02, tx],
                        [m10, m11, m12, ty],
                        [m20, m21, m22, tz],
                    ]
                )
            )

        cutters.append(shape)

    return base.cut(cq.Workplane(obj=cq.Compound.makeCompound(cutters)))


def labelled_ring(od, wall, height):
    """A plain ring with its OD engraved outside and its ID engraved inside.

    The two labels sit 180 degrees apart so both fall in the same cone of sight
    when the part is viewed at an angle.
    """
    inner_d = od - 2 * wall
    ring = cq.Workplane("XY").circle(od / 2).circle(inner_d / 2).extrude(height)
    ring = engrave_radial_text(ring, f"{od:.0f}", od / 2, +1, height / 2, theta0=0.0)
    ring = engrave_radial_text(
        ring, f"{inner_d:.0f}", inner_d / 2, -1, height / 2, theta0=math.pi
    )
    return ring
