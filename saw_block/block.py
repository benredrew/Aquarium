# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Saw block for square hand-sawn cuts in lumber, cut for a 300mm hacksaw.

A trough the board drops into, with a slot through both of its walls that holds
the blade square to the channel -- square in plan because the slot is normal to
the walls the board registers against, and square in elevation because the slot
is vertical. Neither depends on the user's eye or wrist.

## What makes the cut square

The board is pressed against **one** wall, not trapped between two. Sawn timber
is neither to size nor parallel, so a channel cut to hold both faces would
either refuse the wide end of the tolerance or let a narrow board sit skewed --
and a skewed board is a mitred cut. One reference wall is square whatever the
board measures; see spec/lumber.md.

The blade is held by 24mm of slot -- 12mm of wall either side of the channel,
their centres 109mm apart. That separation, not the thickness, is what holds the
blade in plan: 0.4mm of slop over 109mm is a fifth of a degree, where the same
slop taken over a single 12mm wall would be nearly two.

## Why the blade cannot reach the bench

The floor is in two layers. The lower one is solid; the upper one stops 4mm
short of the cut plane either side, leaving an 8mm relief band running under
the slot the whole width of the block. The blade descends through the board,
breaks out of its underside, and enters that band -- so the cut finishes
cleanly through the last fibres instead of stopping exactly on them.

It then stops. The band is 6mm deep and the blade is a continuous bar, so the
portions of it outside the channel bottom out on the lower floor before the
teeth can reach anything else. The relief is a depth stop as much as a relief:
the block cannot be sawn through, and there is 9mm of floor left under the
blade at its lowest.

## Why the bench-hook cleat is a separate part

A bench hook needs something hanging below the surface it stands on, and on a
one-piece block that makes the entire floor underside an overhang printed in
mid-air. So the lip is a cleat that slides into a dovetail groove in the
underside instead, running the full length of the block.

The groove sits under the toe, entirely below where the blade can reach -- the
relief band stops the teeth 7mm above the groove's ceiling -- so the cleat runs
straight through the cut plane in one piece with nothing to clear.

The dovetail is doing real work, not just holding the cleat on. A groove running
along the block constrains the cleat in Y and Z absolutely, which is the whole
of the load: the push stroke drives the block forward, the bench edge bears on
the cleat's back face, and the thrust crosses the joint through the flanks. Slid
home it is one part, and the only thing left to friction is the cleat wandering
along its own length, which nothing pushes it to do.

## The dovetail, and printing it

Flanks at 60 degrees from horizontal, which is the DFM figure both parts want at
once. In the block the groove widens going up, so every layer of its walls sits
on more material than the one below -- no overhang at all, only a 14mm bridge
across the ceiling. In the cleat the same flanks lean out at 30 degrees off
vertical, comfortably inside what prints unsupported. Both parts print in the
orientation they are used in, flat on their own footing, with no supports.

Two allowances, and they are different on purpose. The flanks get
`dovetail_slide_flank`, normal to the face. The ceiling gets more, because the
cleat has to seat on its shoulders against the block's underside -- if the tail
bottomed out on the ceiling first, the two parts would rock on it and the lip
would sit proud of the bench. That is spec/fits.md's own rule: clearance on the
walls a part slides along, none under the face it beds down on.

The groove mouth is chamfered 0.5mm. That is the one place the fit meets the
block's first layer, where the squash of the first extrusion would otherwise
narrow the mouth by an unpredictable fraction and jam a tail cut to fit it.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
from cadkit.engrave import engrave_planar_text
import print_volume
import specs
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Interfaces ----------------------------------------------------------
BLADE_KERF = specs.figure("hacksaw", "blade_kerf")
BLADE_DEPTH = specs.figure("hacksaw", "blade_depth")
FRAME_DEPTH = specs.figure("hacksaw", "frame_depth")
STOCK_T = specs.figure("lumber", "max_thickness")
STOCK_W = specs.figure("lumber", "max_width")
SLOT_SIDE = specs.figure("fits", "blade_slot_side")
CHANNEL_SIDE = specs.figure("fits", "stock_channel_side")
SLIDE_FLANK = specs.figure("fits", "dovetail_slide_flank")

# --- Design parameters ---------------------------------------------------
# As long as the bed will take, read from the bed rather than copied off it:
# length is the one dimension here with nothing to trade against, since the
# board is supported and registered along every millimetre of it.
LENGTH = print_volume.BED_X
WALL = 12.0  # guide wall thickness, and so half the slot's bearing length
FLOOR = 15.0  # floor top is the board's rest face
RELIEF_DEPTH = 4.0  # blade overtravel below the board, and the depth stop
RELIEF_WIDTH = 8.0  # relief band across the cut plane
GUIDE_ABOVE = 22.0  # wall standing proud of the tallest board
GUIDE_BAND = 40.0  # length of wall kept at full height
TAPER = 30.0  # 45 degrees down from the band to the fence, each side
CORNER_RELIEF = 2.0  # dust groove in the floor along each wall

TOE_REACH = 22.0  # floor carried forward to host the dovetail, and the cleat
LIP_DROP = 12.0  # how far the cleat hangs below the bench surface
DOVETAIL_DEPTH = 4.0
DOVETAIL_MOUTH = 10.0  # width at the underside, before the mouth chamfer
DOVETAIL_ANGLE = 60.0  # flank, from horizontal: self-supporting either way up
MOUTH_CHAMFER = 0.5  # first-layer squash relief at the groove mouth
CEILING_GAP = 0.3  # so the tail cannot seat before the shoulders do

LABEL_AT = -25.0  # clear of the cut plane, on the full-height wall

# --- Derived geometry ----------------------------------------------------
CHANNEL = STOCK_W + 2 * CHANNEL_SIDE
SLOT = BLADE_KERF + 2 * SLOT_SIDE
WALL_HEIGHT = STOCK_T + GUIDE_ABOVE  # above the floor
TOP_Z = FLOOR + WALL_HEIGHT
END_HEIGHT = WALL_HEIGHT - TAPER  # wall height above the floor at each end

CHANNEL_Y = CHANNEL / 2  # inner wall faces
OUTER_Y = CHANNEL_Y + WALL  # outer wall faces
TOE_Y = -(OUTER_Y + TOE_REACH)  # front face of the toe
HALF = LENGTH / 2
BAND_HALF = GUIDE_BAND / 2
# Where the taper meets the fence. Its own segment, so TAPER stays the angle it
# claims to be: running the slope straight from the band to the block's end
# would flatten it out as the block got longer, and silently at that.
TAPER_AT = BAND_HALF + TAPER
RELIEF_HALF = RELIEF_WIDTH / 2
FLOOR_SPLIT = FLOOR - RELIEF_DEPTH  # top of the solid lower layer

# The dovetail, taken from its mouth upward. The chamfer eats into the depth the
# flanks have to work with, so the top width is measured from where the chamfer
# leaves off rather than from the underside.
RUN = 1.0 / math.tan(math.radians(DOVETAIL_ANGLE))  # Y gained per mm of rise
REACH_OFF = SLIDE_FLANK / math.sin(math.radians(DOVETAIL_ANGLE))  # normal -> Y
FLANK_RISE = DOVETAIL_DEPTH - MOUTH_CHAMFER
DOVETAIL_TOP = DOVETAIL_MOUTH + 2 * FLANK_RISE * RUN
CLEAT_BACK = -OUTER_Y  # face the bench edge bears on
DOVETAIL_Y = (TOE_Y + CLEAT_BACK) / 2  # groove centred in the toe
TAIL_TOP = DOVETAIL_DEPTH - CEILING_GAP
# Tail half-widths, on flanks parallel to the groove's and REACH_OFF inside them.
# The flank leans out as it rises, so the tail is at its narrowest at the
# shoulder, below where the groove's own flank starts.
TAIL_AT_SHOULDER = DOVETAIL_MOUTH / 2 - REACH_OFF - MOUTH_CHAMFER * RUN
TAIL_AT_TOP = DOVETAIL_MOUTH / 2 - REACH_OFF + (TAIL_TOP - MOUTH_CHAMFER) * RUN

# What the saw has to be able to do, and what the block guarantees.
BLADE_LOW_Z = FLOOR_SPLIT  # lowest the blade can descend
FRAME_NEEDED = TOP_Z - BLADE_LOW_Z  # bow clearance to finish a cut
BENCH_GAP = FLOOR_SPLIT  # floor left under the blade at full depth
SLOT_SPAN = CHANNEL + WALL  # the two bearing bands, centre to centre
REACH = 2 * OUTER_Y  # how far across the blade must cut


def _slab(x0, x1, y0, y1, z0, z1):
    """An axis-aligned box from two opposite corners."""
    return (
        cq.Workplane("XY")
        .workplane(offset=z0)
        .moveTo(x0, y0)
        .rect(x1 - x0, y1 - y0, centered=False)
        .extrude(z1 - z0)
    )


def floor_layers():
    """The two-layer floor: solid below, relieved across the cut plane above.

    Built as a union rather than a pocket cut so the relief band's faces are
    real from the start. The band runs the full width -- under the walls and the
    toe as well as the channel -- because the blade is one bar: whatever depth
    it reaches in the channel it reaches everywhere along its length.
    """
    lower = _slab(-HALF, HALF, TOE_Y, OUTER_Y, 0, FLOOR_SPLIT)
    left = _slab(-HALF, -RELIEF_HALF, TOE_Y, OUTER_Y, FLOOR_SPLIT, FLOOR)
    right = _slab(RELIEF_HALF, HALF, TOE_Y, OUTER_Y, FLOOR_SPLIT, FLOOR)
    return lower.union(left).union(right)


def wall(y_hi):
    """One guide wall, full height over the band and tapered to each end.

    The profile is drawn in the wall's own plane and extruded across its
    thickness, so the 45 degree tapers are exact rather than a chamfer whose
    setback has to be trusted.

    `y_hi` is the wall's face at higher Y, because the extrusion runs along the
    plane normal and that normal is -Y. So the +Y wall is asked for by its outer
    face and the -Y wall by its inner one -- naming them by side instead reads
    better right up until it silently puts one wall a thickness out.
    """
    plane = cq.Plane(origin=(0, y_hi, 0), xDir=(1, 0, 0), normal=(0, -1, 0))
    fence = FLOOR + END_HEIGHT
    profile = [
        (-HALF, FLOOR),
        (-HALF, fence),
        (-TAPER_AT, fence),
        (-BAND_HALF, TOP_Z),
        (BAND_HALF, TOP_Z),
        (TAPER_AT, fence),
        (HALF, fence),
        (HALF, FLOOR),
    ]
    return cq.Workplane(plane).polyline(profile).close().extrude(WALL)


def blade_slot():
    """The guide slot: through both walls, stopping in the relief band's air.

    Its lower end sits 1mm inside that band rather than flush with the walls'
    underside, so the cut passes cleanly out of solid material instead of
    finishing on a face coplanar with it.
    """
    return _slab(
        -SLOT / 2, SLOT / 2, TOE_Y - 10, OUTER_Y + 10, FLOOR_SPLIT + 1, TOP_Z + 10
    )


def corner_grooves():
    """A dust groove along each wall, at the channel's bottom corners.

    A board seats on the floor and registers on a wall, and a sharp internal
    corner between the two is where sawdust and a printed corner bead collect
    to lift it off one or the other. The groove is cut into the floor, not the
    wall, so the registering face stays full height.
    """
    groove = None
    for sign in (+1, -1):
        inner = sign * CHANNEL_Y
        near = inner - sign * CORNER_RELIEF
        cut = _slab(
            -HALF,
            HALF,
            min(inner, near),
            max(inner, near),
            FLOOR - CORNER_RELIEF,
            FLOOR + 1,
        )
        groove = cut if groove is None else groove.union(cut)
    return groove


def _along_block(profile):
    """A closed (Y, Z) profile run the full length of the block.

    The plane is built by hand rather than taken from `cq.Workplane("YZ")` so
    the local axes are known: xDir +Y and normal +X give a derived yDir of +Z,
    which makes the profile read in the same (Y, Z) the rest of the file does.
    """
    plane = cq.Plane(origin=(-HALF, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))
    return cq.Workplane(plane).polyline(profile).close().extrude(LENGTH)


def dovetail_groove():
    """The groove in the underside, mouth chamfered, open at both ends.

    Carried 1mm below the underside so the cut leaves the part through open air
    rather than finishing flush with the face it opens onto.
    """
    mouth = DOVETAIL_MOUTH / 2
    top = DOVETAIL_TOP / 2
    return _along_block(
        [
            (DOVETAIL_Y - mouth - MOUTH_CHAMFER, -1.0),
            (DOVETAIL_Y - mouth, MOUTH_CHAMFER),
            (DOVETAIL_Y - top, DOVETAIL_DEPTH),
            (DOVETAIL_Y + top, DOVETAIL_DEPTH),
            (DOVETAIL_Y + mouth, MOUTH_CHAMFER),
            (DOVETAIL_Y + mouth + MOUTH_CHAMFER, -1.0),
        ]
    )


def build_block():
    block = floor_layers().union(wall(OUTER_Y)).union(wall(-CHANNEL_Y))
    block = block.cut(blade_slot())
    block = block.cut(corner_grooves())
    block = block.cut(dovetail_groove())

    # The capacity on the wall the board is registered against, and the slot
    # width on the other -- the slot is the figure that will move when a printed
    # block is offered up to the real blade, so it wants to be readable on the
    # part rather than looked up.
    block = engrave_planar_text(
        block,
        f"{STOCK_T:.0f} x {STOCK_W:.0f}",
        (LABEL_AT, OUTER_Y, FLOOR + 30.0),
        normal=(0, 1, 0),
        x_dir=(-1, 0, 0),
    )
    block = engrave_planar_text(
        block,
        f"{SLOT:.1f}",
        (LABEL_AT, -OUTER_Y, FLOOR + 30.0),
        normal=(0, -1, 0),
        x_dir=(1, 0, 0),
    )
    return block


def build_cleat():
    """The bench-hook cleat: one bar, the tail above the shoulders, lip below.

    Drawn as a single closed section and run the length of the block. It spans
    the toe exactly, so its back face lands on the -Y wall's outer face: that is
    the face the bench edge bears on, and everything in front of it hangs clear
    over the edge.

    The flanks are the groove's own, moved REACH_OFF in Y, which is the flank
    allowance taken normal to a face at this angle. Cutting the tail to a
    nominal width and clearing it horizontally instead would leave the gap wider
    than intended by a factor of sin(60), and the slide slack by the same.
    """
    return _along_block(
        [
            (TOE_Y, -LIP_DROP),
            (TOE_Y, 0.0),
            (DOVETAIL_Y - TAIL_AT_SHOULDER, 0.0),
            (DOVETAIL_Y - TAIL_AT_TOP, TAIL_TOP),
            (DOVETAIL_Y + TAIL_AT_TOP, TAIL_TOP),
            (DOVETAIL_Y + TAIL_AT_SHOULDER, 0.0),
            (CLEAT_BACK, 0.0),
            (CLEAT_BACK, -LIP_DROP),
        ]
    )


def on_bed(shape):
    """`shape` centred on the bed and sitting on it, for the export."""
    xmin, ymin, zmin, xmax, ymax, zmax = print_volume.bounds(shape)
    return shape.translate((-(xmin + xmax) / 2, -(ymin + ymax) / 2, -zmin))


block = build_block()
cleat = build_cleat()

print_block = on_bed(block)
# Not turned over: the cleat is used lip-down and prints lip-down, its widest
# face on the bed and the tail's flanks leaning out well inside what carries.
print_cleat = on_bed(cleat)

if __name__ == "__main__":
    show_object(
        block,
        name="saw_block",
        options={"color": (215, 170, 105), "alpha": 1.0},
        clear=True,
        reset_camera="reset",
    )
    show_object(
        cleat,
        name="saw_block_cleat",
        options={"color": (95, 120, 150), "alpha": 1.0},
    )

    bx, by, bz = print_volume.extents(print_block)
    cx, cy, cz = print_volume.extents(print_cleat)
    print(f"capacity     {STOCK_T:g} thick x {STOCK_W:g} wide, and anything under it")
    print(f"channel      {CHANNEL:g} wide ({CHANNEL_SIDE:g} a side), board on one wall")
    print(f"slot         {SLOT:g} wide over a {BLADE_KERF:g} set ({SLOT_SIDE:g} a side)")
    print(f"guide        {2 * WALL:g} of slot, walls {SLOT_SPAN:g} apart")
    print(f"wall         {WALL_HEIGHT:g} above the floor, {GUIDE_ABOVE:g} over the board")
    print(f"             full height over {GUIDE_BAND:g} at the cut, 45 deg down to a"
          f" {END_HEIGHT:g} fence for the last {LENGTH - 2 * TAPER_AT:g}")
    print(f"length       {LENGTH:g}, the bed's own {print_volume.BED_X:g}")
    print(f"blade cut    {REACH:g} across, descending to {BLADE_LOW_Z:g} above the bench")
    print(f"overtravel   {RELIEF_DEPTH:g} past the board, then the floor stops it")
    print(f"frame needs  {FRAME_NEEDED:g} bow clearance; spec says {FRAME_DEPTH:g}"
          f" -- {'clears' if FRAME_DEPTH >= FRAME_NEEDED else 'DOES NOT CLEAR'}")
    print(f"bench gap    {BENCH_GAP:g} of floor under the blade at full depth")
    print(f"cleat        {LENGTH:g} long, {LIP_DROP:g} lip,"
          f" back face bearing on the bench edge at y={CLEAT_BACK:g}")
    print(f"dovetail     {DOVETAIL_MOUTH:g} mouth -> {DOVETAIL_TOP:.2f} at"
          f" {DOVETAIL_DEPTH:g} deep, flanks {DOVETAIL_ANGLE:g} deg")
    print(f"slide fit    {SLIDE_FLANK:g} normal to each flank"
          f" ({REACH_OFF:.3f} measured across), {CEILING_GAP:g} over the tail")
    print(f"             {MOUTH_CHAMFER:g} mouth chamfer;"
          f" {FLOOR_SPLIT - DOVETAIL_DEPTH:g} of floor between it and the blade")
    print(f"block        {bx:.2f} x {by:.2f} x {bz:.2f} mm"
          f" -- {'fits' if print_volume.fits(print_block) else 'DOES NOT FIT'}")
    print(f"cleat        {cx:.2f} x {cy:.2f} x {cz:.2f} mm"
          f" -- {'fits' if print_volume.fits(print_cleat) else 'DOES NOT FIT'}")

    if print_volume.fits(print_block) and print_volume.fits(print_cleat):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(print_block, str(OUTPUT_DIR / "saw_block.step"))
        cq.exporters.export(print_cleat, str(OUTPUT_DIR / "saw_block_cleat.step"))
    else:
        print("not exported: a part is outside the build volume")
