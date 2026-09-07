# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""A 45 degree arc of the cradle, for checking the seat's curvature by eye.

The cradle fitting the glass confirmed the vessel's base *diameter*. It said
little about the corner radius: the vessel drops onto the seat and stops, and it
will do that over a range of seat curvatures without the error being visible or
felt. This part is offered up to the vessel's own corner and the two curves
compared directly, which is the only cheap way to see the difference.

Cut from the full ring, from an arc the build plate never reaches. That matters
-- on the four axes the plate trims the cradle back to r=90 and the section
there is not the design section, so a segment taken from those zones would be
comparing the wrong shape. The window where the ring survives at full radius is
computed below rather than assumed, and the arc is centred in it.

Everything comes from bowl.py: same cavity radius, same seat arc, same wall. No
dimension is restated here, so this piece cannot test a shape the cradle does
not have.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import engrave as engrave_module
import print_volume
from engrave import engrave_radial_text
from ocp_vscode import show_object, set_port

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"


def load_part(relative_path, name):
    """Import bowl.py for its geometry only (no viewer/export)."""
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parent / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bowl = load_part("bowl.py", "bowl")

ARC = 45.0  # degrees of vessel circumference this piece grips

# --- Where the section is whole -------------------------------------------
# The plate reaches r = (BED_X/2) / max(|cos t|, |sin t|). The ring keeps its
# full OUTER_R wherever that is the larger of the two, which works out to a
# window centred on each diagonal. Solved rather than eyeballed, because the
# margin either side is what makes the piece worth printing at all.
_REACH = (print_volume.BED_X / 2) / bowl.OUTER_R
# The first angle off the axis at which the plate stops biting: cos t = _REACH.
# Past 45 degrees the sine takes over, so the window is symmetric about the
# diagonal and this is its half-width measured from there. If the whole ring
# already fits the bed there is no bitten zone and every angle qualifies.
WINDOW_HALF = (
    45.0 - math.degrees(math.acos(_REACH)) if _REACH < 1.0 else 45.0
)

CENTRE_ANGLE = 45.0  # the first diagonal, midway between two flats
MARGIN = WINDOW_HALF - ARC / 2  # clear degrees either side of the arc

# Two lines of label, placed symmetrically about the wall's mid-height. The
# outer wall is a plain cylinder for the whole height -- only the inside is
# shaped -- so both lines have material behind them wherever they sit.
#
# Deliberately not bowl.LABEL_Z. That figure centres a single label on the
# straight band above the seat tangent, so it climbs as the corner radius grows:
# at R8.2 it reaches 10.1 and leaves a 3.66mm line 0.07mm short of the top face.
# Here the pair is placed from the height and the font instead, so the labels
# stay clear whatever the radius under test happens to be.
LABEL_LINE_HEIGHT = (
    cq.Workplane("XY")
    .text("8", engrave_module.FONT_SIZE, 1.0, combine=False, kind="bold")
    .val()
    .BoundingBox()
    .ylen
)  # 3.66 -- inked height of a digit, measured rather than assumed
LABEL_GAP = 1.5  # clear millimetres between the two lines
_LABEL_OFFSET = (LABEL_LINE_HEIGHT + LABEL_GAP) / 2
LABEL_Z_UPPER = bowl.HEIGHT / 2 + _LABEL_OFFSET
LABEL_Z_LOWER = bowl.HEIGHT / 2 - _LABEL_OFFSET


def segment():
    """The arc, cut from the unclipped ring and tidied like the ring itself."""
    wedge = bowl.sector(ARC, bowl.OUTER_R + 5, bowl.HEIGHT, CENTRE_ANGLE)
    piece = bowl.ring.intersect(wedge)

    # Same 0.3mm break on the vertical corners the ring gets, including the two
    # radial ends this cut creates. Rounded before the label goes on, because
    # engraved text is full of Z-parallel edges of its own.
    piece, skipped = bowl.round_vertical_corners(piece, bowl.EDGE_ROUND)

    # Both figures that define the cavity, on the outer wall at the centre of
    # the arc. Stacked rather than side by side: the text is stretched 200%
    # circumferentially, so "ID 178.4" alone spends 29.7 of the 45 degrees and
    # the two will not sit next to each other.
    #
    # These are the part's own figures, not the vessel's. The seat is cut 0.2
    # larger than the glass it takes, so engraving the vessel's radius here
    # would put a number on the object that the object does not have -- the
    # exact misreading the labelling convention exists to stop. Take 2*CLEARANCE
    # off the ID and CLEARANCE off the R to get back to the vessel.
    for text, z in (
        (f"ID {2 * bowl.CAVITY_R:g}", LABEL_Z_UPPER),
        (f"R{bowl.CAVITY_CORNER_RADIUS:g}", LABEL_Z_LOWER),
    ):
        piece = engrave_radial_text(
            piece, text, bowl.OUTER_R, +1, z, theta0=math.radians(CENTRE_ANGLE)
        )
    return piece, skipped


part, UNROUNDED_CORNERS = segment()

if __name__ == "__main__":
    show_object(part, name="cradle_segment", clear=True)
    print_volume.show(show_object)

    print(f"full-section window : {45 - WINDOW_HALF:.2f} to {45 + WINDOW_HALF:.2f} deg")
    print(f"this arc            : {CENTRE_ANGLE - ARC / 2:.2f} to "
          f"{CENTRE_ANGLE + ARC / 2:.2f} deg")
    print(f"clear either side   : {MARGIN:.2f} deg")
    if UNROUNDED_CORNERS:
        print(f"corners left sharp  : {UNROUNDED_CORNERS}")

    dx, dy, dz = print_volume.extents(part)
    print(f"segment: {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{len(part.val().Solids())} body, "
          f"{part.val().Volume() / 1000:.1f} cm3")

    if MARGIN <= 0:
        print("NOT exported: the arc runs into the zone the build plate trims.")
    elif not print_volume.fits(part):
        print("NOT exported: does not fit the build volume.")
    else:
        cq.exporters.export(part, str(OUTPUT_DIR / "cradle_segment.step"))
        print("  wrote cradle_segment.step")
