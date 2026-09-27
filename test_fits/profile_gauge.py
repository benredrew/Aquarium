# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""A flat swatch whose one edge is the vessel's profile, to check it against glass.

Everything in `vessel/vessel.py` came off a photograph. The base OD is confirmed
and the top opening ID is confirmed; the other four diameters, all five junction
heights and the overall height are scaled from an outline and have never been
put against the object. This is the part that does that.

## Why one tall piece rather than a ring per band

A ring confirms one diameter and says nothing about where that diameter sits. The
profile's real risk is not any single diameter -- it is the stack: five junction
heights built downward from the rim and upward from the crest, with the body
absorbing the slack between them. An error in the neck moves every junction above
it while leaving every diameter correct, and no ring would ever show it.

So this is one piece from the contact plane to the rim, standing on the table the
vessel stands on. z = 0 is the same plane for both, which makes every height on
the gauge a direct comparison rather than a measurement.

## How to read it

Hold it against the glass in a vertical plane, slide it in until it touches, and
backlight it. Light between the edge and the glass is the model being too narrow
there; a band that stops the gauge before the rest touches is the model being too
wide there. Then:

    top edge above the rim         HEIGHT is over
    top edge below the rim         HEIGHT is under
    touches at both waists only    the body diameter is over
    touches at the body only       the waists are under

Both waists are one figure used twice, so if only the lower one gaps, that is the
lower waist's *height* being wrong rather than its diameter -- the substrate line
crosses it in the photograph and it is the weakest part of the model.

The contact edge starts 2mm above the table, not at it: the base tongue is
trimmed off as unprintable (see TONGUE_MIN). Nothing is lost that this part was
going to settle -- the base roll is the confirmed end of the profile -- but do
not read the bottom 2mm as a gap.

Being off the axial plane is forgiving: held 5mm off-centre the gauge reads a
90mm radius 0.14mm small, which is well under the errors being hunted.

## What it is cut with

The vessel solid itself, from `vessel/vessel.py` -- not a copy of the profile.
The unlabelled solid: the labelled one carries 0.3mm engraving pockets at this
exact angle, and cutting with those would leave letter-shaped bumps standing
proud of the contact edge.

Cutting with the *solid* rather than an extruded meridian is what makes the edge
seatable. The swatch has thickness, and its faces sit 1.5mm either side of the
axial plane, where the glass has already fallen away; taking the cut from the
solid gives back a 0.013mm crown that lets the edge sit down instead of riding on
its two corners. The number is verified below rather than asserted.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # shared engrave

import cadquery as cq
import engrave
import print_volume
from cadkit.viewer import show as show_object
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.TopoDS import TopoDS

OUTPUT_DIR = Path(__file__).parent / "output"


def load_part(relative_path, name):
    """Import vessel.py for its geometry only (no viewer/export)."""
    path = Path(__file__).resolve().parent.parent / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vessel_mod = load_part("vessel/vessel.py", "vessel")

# --- The swatch -----------------------------------------------------------
THICKNESS = 1.0    # 5 layers at 0.2
WEB = 18.0         # material behind the widest point, the rim

# The profile's whole radial swing is under 10mm, so the web is what makes this
# a rigid object rather than a ribbon. It also has to carry the labels: a digit
# at engrave.FONT_SIZE is ~2.8mm wide, so a five-character diameter needs ~12.4.
LABEL_MARGIN = 2.0     # from the back edge to the end of the longest label
LABEL_DEPTH = engrave.ENGRAVE_DEPTH

MAX_R = vessel_mod.RIM_DIA / 2                  # 90.7, the widest point
MIN_R = vessel_mod.FLAT_DIA / 2                 # 81.0, the base flat
BACK_R = MAX_R + WEB
INNER_R = MIN_R - 6.0    # starts inside the narrowest point; all of it is cut away
WIDTH = BACK_R - INNER_R
HEIGHT = vessel_mod.HEIGHT

# The vessel's own end faces sit exactly on z=0 and z=HEIGHT, which are also the
# swatch's two ends. Cutting coplanar face against coplanar face is the one
# boolean OCC is entitled to be vague about, so the cutter is run past both ends
# on the diameter it has there -- the base flat below, the rim above.
CUTTER_OVERRUN = 5.0


def cutter():
    """The vessel, unlabelled, extended past both ends of the swatch."""
    below = (
        cq.Workplane("XY")
        .workplane(offset=-CUTTER_OVERRUN)
        .circle(vessel_mod.FLAT_DIA / 2)
        .extrude(CUTTER_OVERRUN)
    )
    above = (
        cq.Workplane("XY")
        .workplane(offset=HEIGHT)
        .circle(vessel_mod.RIM_DIA / 2)
        .extrude(CUTTER_OVERRUN)
    )
    return vessel_mod.build_vessel().union(below).union(above)


def blank():
    """The rectangle, standing in the XZ plane, centred on it in thickness."""
    return (
        cq.Workplane("XZ")
        .moveTo(INNER_R, 0)
        .rect(WIDTH, HEIGHT, centered=False)
        .extrude(THICKNESS / 2, both=True)
    )


# --- Corners --------------------------------------------------------------
# A 0.4mm nozzle cannot turn a sharp external corner: it rounds it anyway, and
# over-extrudes into a bulge doing it. Rounding it in the model instead puts the
# corner somewhere known, at a radius the nozzle can actually walk.
#
# Only the corners of the swatch's outline -- the edges running through the
# thickness, normal to the two big faces. Laid down to print those are the
# Z-parallel ones, traced by the nozzle on every single layer, which is what
# makes them worth rounding and the profile edge's own curvature not.
CORNER_DIA = 2.0
CORNER_R = CORNER_DIA / 2

# Three of the four corners are ordinary. The fourth, at the foot of the contact
# edge, is not a corner at all: the base roll arrives at z=0 tangent to the
# table, so the swatch runs out to a feather there -- zero thickness at r=81.0,
# and not one extrusion width until r=83.5. A fillet cannot help, because a
# fillet needs an included angle and this has none; rounding a cusp with a
# tangent arc only moves the cusp along.
#
# So the tongue is trimmed back to where it is worth printing, which leaves a
# real corner that rounds like the other three. It is cut at the height where a
# plain cylinder meets the roll tangentially, so nothing above it moves.
#
# The cost is the bottom TONGUE_MIN of contact, all of it base roll -- the one
# part of the profile already confirmed (spec/vessel.md: the OD by the cradle,
# the R8 by the 45 degree sections). It is the cheapest 2mm on the part to give
# up, and the z=0 datum is untouched: the swatch still stands on the table on a
# full-width foot.
# Three corner radii, not two: the trim face is rounded at *both* ends -- into
# the base below, into the roll above -- so at 2*CORNER_R the two rounds meet
# with no face left between them and the upper one refuses to build. This leaves
# a corner radius of straight wall in the middle.
TONGUE_MIN = 3 * CORNER_R
_ROLL_R = vessel_mod.CORNER_R
TONGUE_TRIM_R = MIN_R + math.sqrt(_ROLL_R ** 2 - (_ROLL_R - TONGUE_MIN) ** 2)


def trim_base_tongue():
    """A plain cylinder, up to the height it goes tangent to the base roll."""
    return (
        cq.Workplane("XY")
        .workplane(offset=-1.0)
        .circle(TONGUE_TRIM_R)
        .extrude(1.0 + TONGUE_MIN)
    )


def round_outline_corners(shape, radius):
    """Round the outline's corners, the ones normal to the swatch's faces.

    Not selected by direction. Only two of the four corners are straight lines
    running through the thickness; the swatch has 3mm of it, so where the
    contact surface meets the top and bottom faces the corner is an *arc* of
    the vessel's own radius, and a `|Y` filter walks straight past it. That
    filter found two corners, rounded them, and reported success.

    Selected by what meets what instead. Every corner here is a planar face --
    the back, the top, the base -- meeting something else, so an edge qualifies
    if it lies on a plane that is not one of the two broad faces, and does not
    lie in a broad face itself. That excludes the outline curves, which are the
    broad faces' own boundaries, and it excludes the dozen tangent seams
    between the profile's cylinders, tori and cone: those look exactly like
    corners to a direction filter and rounding one would cut a groove across an
    otherwise smooth surface.

    Runs before the labels are cut regardless -- engraved text is nothing but
    edges standing normal to a face.
    """
    solid = shape.val()
    broad = [
        face
        for face in solid.Faces()
        if face.geomType() == "PLANE" and abs(face.normalAt().y) > 0.999
    ]
    on_broad = [edge.wrapped for face in broad for edge in face.Edges()]

    def blend(edges):
        builder = BRepFilletAPI_MakeFillet(solid.wrapped)
        for edge in edges:
            builder.Add(radius, TopoDS.Edge_s(edge.wrapped))
        builder.Build()
        return cq.Shape.cast(builder.Shape())

    keep = []
    for face in solid.Faces():
        if face.geomType() != "PLANE":
            continue
        if any(face.wrapped.IsSame(b.wrapped) for b in broad):
            continue
        for edge in face.Edges():
            if any(edge.wrapped.IsSame(other) for other in on_broad):
                continue
            if any(edge.wrapped.IsSame(k.wrapped) for k in keep):
                continue
            keep.append(edge)

    # And the one corner that touches no plane: where the trim cylinder meets
    # the base roll at z = TONGUE_MIN. Re-entrant, so it cannot bulge, but it is
    # still a corner and it is still cheaper to put it where we chose.
    for edge in solid.Edges():
        centre = edge.Center()
        if (
            abs(centre.z - TONGUE_MIN) < 1e-6
            and abs(math.hypot(centre.x, centre.y) - TONGUE_TRIM_R) < 0.05
            and not any(edge.wrapped.IsSame(k.wrapped) for k in keep)
        ):
            keep.append(edge)

    global ROUNDED_COUNT
    ROUNDED_COUNT = len(keep)
    if not keep:
        return shape, []

    try:
        return cq.Workplane(obj=blend(keep)), []
    except Exception:
        pass

    # One of them will not blend, so find which rather than losing the pass.
    # The likely refusal is the corner at the foot of the contact edge: the base
    # roll arrives at z=0 tangent to the bottom face, so that "corner" has no
    # included angle at all -- it is a feather edge, and a fillet has nothing to
    # sit in. Reported rather than silently dropped, because it is also the
    # sharpest thing on the part and the most in need of the round.
    good, skipped = [], []
    for edge in keep:
        try:
            blend([edge])
            good.append(edge)
        except Exception:
            centre = edge.Center()
            skipped.append((round(centre.x, 2), round(centre.z, 2)))
    if not good:
        return shape, skipped
    return cq.Workplane(obj=blend(good)), skipped


# --- The split -------------------------------------------------------------
# Two pieces, so a wrong diameter can be found and reprinted without waiting on
# the other 90mm. Cut in the middle of the body's straight wall: both halves get
# a plain vertical edge at the join, which is the one place a cut costs nothing
# -- through a blend it would leave each piece ending on a curve with no
# straight wall to sit against.
#
# They register at opposite ends. The lower stands on the table, on the same
# plane the tank does. The upper hangs from the rim, its top face level with the
# glass. Neither carries the other's datum, so the split gives up the one thing
# the tall piece did for free: the cumulative height from base to rim. That is
# no longer a loss -- as of today the height is measured (spec/vessel.md), and a
# rule does it better than a gauge would.
SPLIT_Z = sum(vessel_mod.wall_span(2)) / 2

HALVES = (
    ("lower", 0.0, SPLIT_Z, "stands on the table"),
    ("upper", SPLIT_Z, HEIGHT, "top face level with the rim"),
)


def half(shape, z_lo, z_hi):
    """`shape` clipped to one piece's band of heights."""
    band = (
        cq.Workplane("XY")
        .workplane(offset=z_lo)
        .circle(BACK_R + 5)
        .extrude(z_hi - z_lo)
    )
    return shape.intersect(band)


def engrave_face_text(shape, txt, x, z):
    """Cut `txt` into the +Y face, upright, reading the way the swatch is held.

    Viewed from +Y with Z up, the viewer's right hand is world -X, so the text
    advances that way; the plane's yDir then comes out +Z on its own and the
    digits stand up without being told to.
    """
    plane = cq.Plane(
        origin=(x, THICKNESS / 2, z), normal=(0, 1, 0), xDir=(-1, 0, 0)
    )
    cutter_ = (
        cq.Workplane(plane)
        .workplane(offset=-LABEL_DEPTH)
        .text(
            txt,
            engrave.FONT_SIZE,
            LABEL_DEPTH + engrave.OVERSHOOT,
            combine=False,
            kind="bold",
            halign="center",
            valign="center",
            fontPath=engrave.FONT_PATH,
        )
    )
    return shape.cut(cutter_)


def text_width(txt):
    """Inked width of `txt` at the shared font size, measured not assumed."""
    return (
        cq.Workplane("XY")
        .text(txt, engrave.FONT_SIZE, 1.0, combine=False, kind="bold",
              fontPath=engrave.FONT_PATH)
        .val()
        .BoundingBox()
        .xlen
    )


def label_gauge(shape, z_lo, z_hi):
    """Each section's diameter, engraved level with the wall it belongs to.

    Right-aligned in a single column against the back edge: the numbers line up,
    and the column stays clear of the profile edge at the rim, where the web is
    at its narrowest. Placing them at the profile edge instead would put them in
    the way of the one part of the part that has a job.

    Clipped to this piece. A wall the split leaves too short to hold a legible
    line loses its label rather than getting one that runs off the end -- the
    body is the only section that can happen to, and it keeps a line on both
    sides of the cut.
    """
    pad = vessel_mod.LABEL_HEIGHT / 2 + 1.0
    labels = []
    for i, (_name, dia, z0, _z1) in enumerate(vessel_mod.SECTIONS):
        lo, hi = vessel_mod.wall_span(i)
        # Same rule vessel.py labels by: the bulge has no straight wall, its
        # crest is a tangent point, so its label goes on the crest height.
        if hi - lo < vessel_mod.LABEL_HEIGHT:
            lo = hi = z0
        lo, hi = max(lo, z_lo + pad), min(hi, z_hi - pad)
        if hi < lo:
            continue
        z = (lo + hi) / 2
        txt = f"{dia:.1f}"
        x = BACK_R - LABEL_MARGIN - text_width(txt) / 2
        shape = engrave_face_text(shape, txt, x, z)
        labels.append((txt, x, z))
    return shape, labels


whole = blank().cut(cutter()).cut(trim_base_tongue())


def lay_flat(part):
    """Rotating +90 about X brings the labelled +Y face up, so the text prints
    as a top surface rather than against the bed, and the profile edge becomes
    an XY contour where the printer is most accurate."""
    return part.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 0, THICKNESS / 2))


PIECES = {}
for _name, _lo, _hi, _datum in HALVES:
    _part = half(whole, _lo, _hi)
    _part, _skipped = round_outline_corners(_part, CORNER_R)
    _rounded = ROUNDED_COUNT
    _part, _labels = label_gauge(_part, _lo, _hi)
    PIECES[_name] = {
        "part": _part,
        "flat": lay_flat(_part),
        "span": (_lo, _hi),
        "datum": _datum,
        "labels": _labels,
        "skipped": _skipped,
        "rounded": _rounded,
    }

lower = PIECES["lower"]["part"]
upper = PIECES["upper"]["part"]


# --- Verification ---------------------------------------------------------
# A slab has height, so on a sloping part of the profile it spans a range of
# radii: the vessel's widest row in the slab is its top and the swatch's nearest
# row is its bottom, and the difference between them is the slab, not the part.
# Kept thin enough that the worst of that is a fifth of the crown being measured.
SLAB = 0.02


def _slab(z, r):
    return (
        cq.Workplane("XY").workplane(offset=z - SLAB / 2).circle(r).extrude(SLAB)
    )


def edge_radius(shape, z):
    """Nearest the axis `shape` comes in a thin slab at height `z`, or None.

    From the optimal bounding box, not from vertices -- the contact edge is a
    curved surface and its nearest row is not a vertex of it.
    """
    cut = shape.intersect(_slab(z, BACK_R + 1))
    if not cut.val().Solids():
        return None
    return print_volume.bounds(cut)[0]


def wall_radius(shape, z):
    """The vessel's widest row in the same slab -- the radius there."""
    return print_volume.bounds(shape.intersect(_slab(z, BACK_R + 1)))[3]


def slab_allowance(z):
    """How much of a gap the slab's own height can account for at `z`.

    A blend of radial step d over height T turns through alpha = 2*atan(d/T)
    and is steepest at its inflection, where dr/dz is tan(alpha/2) = d/T. The
    junctions are sampled at exactly that inflection, so this is the worst case
    rather than a typical one.
    """
    for zj, T in vessel_mod.TRANSITIONS.items():
        if abs(z - zj) < 1e-9:
            below = next(d for _n, d, _a, b in vessel_mod.SECTIONS if abs(b - zj) < 1e-9)
            above = next(d for _n, d, a, _b in vessel_mod.SECTIONS if abs(a - zj) < 1e-9)
            return abs(below - above) / 2 / T * SLAB
    return 0.0


def sample_heights():
    """Every junction, plus the middle of every straight wall."""
    zs = []
    for i, (_n, _d, z0, z1) in enumerate(vessel_mod.SECTIONS):
        lo, hi = vessel_mod.wall_span(i)
        zs.append(("crest" if i == 0 else "junction", z0))
        if hi - lo > 1.0:
            zs.append(("wall", (lo + hi) / 2))
    # Stopping clear of the corner round: inside it the edge is deliberately no
    # longer the vessel's outline, so a sample there would report the round as
    # an error.
    zs.append(("under top round", HEIGHT - CORNER_R - 0.2))
    return zs


if __name__ == "__main__":
    # The lower piece alone, against the ghost of the tank it came out of.
    show_object(lower, name="profile_gauge_lower",
                options={"color": (255, 200, 90), "alpha": 1.0}, clear=True)
    show_object(vessel_mod.build_vessel(), name="vessel",
                options={"color": (150, 205, 225), "alpha": 0.28})

    vessel_solid = vessel_mod.build_vessel()
    print(f"split at z {SPLIT_Z:.2f}, mid body wall "
          f"({vessel_mod.wall_span(2)[0]:.2f} .. {vessel_mod.wall_span(2)[1]:.2f})")
    print(f"profile swing {MIN_R:.1f} .. {MAX_R:.1f} mm radius, "
          f"{THICKNESS:g}mm thick, web {WEB:g} at the rim")

    for name, lo, hi, datum in HALVES:
        piece = PIECES[name]
        part, flat = piece["part"], piece["flat"]
        dx, dy, dz = print_volume.extents(flat)
        solids = len(part.val().Solids())

        print(f"\n=== {name.upper()}   z {lo:.2f} .. {hi:.2f}   ({datum})")
        print(f"  {dx:.2f} wide x {hi - lo:.2f} tall x {THICKNESS:g} thick, "
              f"{part.val().Volume() / 1000:.1f} cm3, {solids} "
              f"{'body' if solids == 1 else 'BODIES'}")
        print(f"  lying flat  {dx:.2f} x {dy:.2f} x {dz:.2f} on a "
              f"{print_volume.BED_X:g} bed -- "
              f"{'fits' if print_volume.fits(flat) else 'DOES NOT FIT'}")
        print(f"  corners     R{CORNER_R:g}, " + (
            f"{piece['rounded'] - len(piece['skipped'])} of {piece['rounded']}; "
            f"LEFT SHARP at {piece['skipped']}"
            if piece["skipped"] else f"all {piece['rounded']} of them"))
        print("  labels      " + ", ".join(
            f"{t} at z{z:.1f}" for t, _x, z in piece["labels"]))

        # The claim each piece rests on: its edge is the vessel's own outline,
        # nowhere inside it. Interference anywhere seats the gauge on that spot
        # and lifts every other band off the glass.
        try:
            bite = part.intersect(vessel_solid)
            bite_vol = bite.val().Volume() if bite.val().Solids() else 0.0
        except ValueError:
            # OCC hands back a null shape when the two have nothing in common,
            # and cadquery raises rather than casting it. That is the result
            # this test wants; only a *volume* would be a failure.
            bite_vol = 0.0

        print("    where                z      gauge     vessel     gap     crown")
        worst_wall = 0.0
        for what, z in sample_heights():
            if not lo + CORNER_R < z < hi - CORNER_R:
                continue
            g = edge_radius(part, z)
            if g is None:
                continue
            w = wall_radius(vessel_solid, z)
            crown = (w - g) - slab_allowance(z)
            if slab_allowance(z) == 0.0:
                worst_wall = max(worst_wall, abs(crown))
            print(f"    {what:18s} {z:7.2f}  {g:8.3f}  {w:8.3f}  {w - g:+6.4f}  "
                  f"{crown:+7.4f}")

        # Half the thickness off the axial plane the glass has fallen away by
        # r - sqrt(r^2 - (t/2)^2); on a straight wall that is the whole gap.
        predicted = MAX_R - (MAX_R ** 2 - (THICKNESS / 2) ** 2) ** 0.5
        print(f"  crown       {predicted:.4f} predicted on a straight wall, "
              f"{worst_wall:.4f} worst measured")
        print(f"  inside      {bite_vol:.6f} mm3 "
              f"({'clear' if bite_vol < 1e-6 else 'INTERFERENCE'})")

        out = OUTPUT_DIR / f"profile_gauge_{name}.step"
        if not print_volume.fits(flat):
            print("  NOT exported: does not fit the build volume.")
        elif solids != 1:
            print("  NOT exported: the cut left more than one body.")
        else:
            cq.exporters.export(flat, str(out))
            print(f"  wrote       {out.name} (laid flat, labels up)")
