# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""Lid screen -- the single-piece annulus segment that fills the open water
left by the two-spoke lid.

Dropping the LED Sun Lid from six spokes to two opens up nearly the whole
annulus between the hub and the rim. This part fills it: one C-shaped segment
spanning from one spoke round the long way to the other, leaving only the short
arc between the two spokes open, which is where the cable comes out.

Three features, and the names are used consistently here and in conversation:

  screen      the plate roofing the part, SCREEN_THICKNESS thick. Left as solid
              geometry rather than perforated; it is meant to be run in the
              slicer with zero top and bottom layers, so its infill pattern is
              exposed and becomes the mesh. Exported as its own body.
  screen rim  the wall standing round the screen -- inner, outer and both ends
              -- RIM_HEIGHT tall and RIM_THICKNESS thick. Hangs below the
              screen, leaving the underside open.
  screen lip  the flange let into the lid's rebate, which the part hangs on.
              Its thickness is the lid's SCREEN_LIP_DEPTH, since the lid cuts
              the rebate to match.

Everything is referenced down from the top face, which finishes flush with the
lid; the rim's lower edge is wherever RIM_HEIGHT leaves it.

It installs from the top, dropping into the gap, so the rim's lower edge is the
leading edge and carries the chamfer. Same fit-from-top rule the ring light
follows in lid.py: what has to clear is the vertical sweep, not just the seated
envelope. The rim's end faces are vertical surfaces and its walls are vertical,
so the whole part descends without binding.

Built by subtracting the lid from a plain annulus rather than by sweeping an arc
between computed angles. The spoke roots carry CORNER_RADIUS fillets that reach
out along the hub and rim walls into the void, so an arc cut to the spokes' flat
sides would foul them; subtracting the lid takes the fillets into account
exactly, whatever they are set to. The subtraction leaves two pieces -- the long
arc and the short one between the spokes -- and this part is the long one.

The annulus stops at the plain hub and rim cylinders, so it does not reach into
the chamfer reliefs on the lid's top and bottom edges. Those stay as a small V
groove between the two parts rather than being filled by a feather edge that
would not print.
"""
import importlib.util
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cadquery as cq
import print_volume
from cadquery.selectors import Selector
from ocp_vscode import show_object, set_port
from OCP.BRepOffset import BRepOffset_Mode
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
from OCP.GeomAbs import GeomAbs_JoinType

set_port(3939)

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Design parameters ----------------------------------------------------
SCREEN_THICKNESS = 4.0  # the plate that gets run as bare infill
RIM_HEIGHT = 8.0  # rim's full height, measured down from the top face
RIM_THICKNESS = 2.0  # wall thickness of the rim, all four sides
CHAMFER = 0.8  # break on the rim's lower edge, the leading edge on installation

SCREEN_COLOR = (0, 0, 139)  # dark blue -- the solid body
INFILL_COLOR = (120, 190, 235)  # pale blue -- the body run as bare infill
ALPHA = 1.0  # solid


def load_part(relative_path, name):
    """Import a part script for its geometry only (no viewer/export)."""
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parent.parent / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lid_variant = load_part("led_sun_lid/lid_two_spoke.py", "lid_two_spoke")
lid_mod = lid_variant.lid_mod  # the shared dimensions from lid.py

# The joint is dimensioned on the lid side; taken from there rather than
# restated so the rebate and the lip cannot drift apart.
CLEARANCE = lid_mod.SCREEN_CLEARANCE  # 0.2, on the walls only
LIP_DEPTH = lid_mod.SCREEN_LIP_DEPTH  # 2.0, tight in z so the lip finishes flush

# Radial band of the void: hub outside face to rim inside face, held off both.
SCREEN_IR = lid_mod.HUB_OR + CLEARANCE  # 50.95
SCREEN_OR = lid_mod.RIM_IR - CLEARANCE  # 77.30

# Everything hangs off the top face, which is flush with the lid's.
TOP_Z = lid_mod.THICKNESS  # 10.50
RIM_BOTTOM_Z = TOP_Z - RIM_HEIGHT  # 2.50 -- clear of the lid's underside
SCREEN_BOTTOM_Z = TOP_Z - SCREEN_THICKNESS  # 6.50 -- roof of the hollow

assert SCREEN_BOTTOM_Z > RIM_BOTTOM_Z, "screen would be thicker than the rim is tall"
assert LIP_DEPTH <= SCREEN_THICKNESS, "lip would hang below the screen it sits in"

# The blank starts at the nominal void -- hub outside face to rim inside face,
# no clearance -- and the clearance is taken off it by the offset cutter, so it
# lands on every mating face at once.
BLANK_IR = lid_mod.HUB_OR  # 50.75
BLANK_OR = lid_mod.RIM_IR  # 77.50


class BottomEdgesAtRadii(Selector):
    """Edges at height `z` lying wholly on a cylinder of one of the given radii.

    Picks out the two leading edges -- the rim's outside and its inside -- at
    its lower edge, without also catching the edges of the hollow, which do not
    touch the lid on the way in and are left sharp.

    Takes both radii at once because they have to be chamfered in a single
    operation. Chamfering the outer edge first splits the bottom face, and
    faces("<Z") then returns only the piece that does not carry the inner edge,
    so a second pass finds nothing to work on and raises.
    """

    def __init__(self, radii, z, tol=1e-6):
        self.radii = radii
        self.z = z
        self.tol = tol

    def filter(self, objectList):
        keep = []
        for edge in objectList:
            vertices = edge.Vertices()
            if not vertices or any(abs(v.Z - self.z) > self.tol for v in vertices):
                continue
            if any(
                all(abs(math.hypot(v.X, v.Y) - r) < self.tol for v in vertices)
                for r in self.radii
            ):
                keep.append(edge)
        return keep


def offset_sweep(distance):
    """The swept lid grown by `distance` on every face.

    Both halves live in lid.py, which owns the joint's dimensions: sweep_prism
    for the silhouette and offset_solid for the growing. The lid variant has
    already taken the sweep, so it is reused here rather than sectioned again.
    """
    return lid_mod.offset_solid(lid_variant.SWEEP, distance)


def build_screen():
    blank = (
        cq.Workplane("XY")
        .circle(BLANK_OR)
        .circle(BLANK_IR)
        .extrude(RIM_HEIGHT)
        .translate((0, 0, RIM_BOTTOM_Z))
    )

    # Take the clearance off every mating face at once, and trim to the void.
    remainder = blank.cut(offset_sweep(CLEARANCE))

    # The spokes cut the annulus in two. Keep the long arc; the short one is the
    # gap between the spokes where the cable exits. Done before hollowing so
    # what follows runs on a single solid.
    pieces = sorted(remainder.val().Solids(), key=lambda s: s.Volume(), reverse=True)
    unhollowed = cq.Workplane(obj=pieces[0])

    # Hollow it from below, leaving the rim standing round a screen that is
    # thicker than the rim's own wall. A shell cannot do that -- it gives one
    # thickness everywhere -- so it is used only to find the footprint inside
    # the rim, and the hollow is then cut to whatever depth the screen leaves.
    inner = unhollowed.cut(unhollowed.faces("<Z").shell(-RIM_THICKNESS))
    outline = lid_mod.section_outline(inner, RIM_BOTTOM_Z + RIM_THICKNESS / 2)
    pocket = cq.Solid.extrudeLinear(
        outline, [], cq.Vector(0, 0, SCREEN_BOTTOM_Z - (RIM_BOTTOM_Z - 1))
    )
    # Started a millimetre low so the cut does not have to resolve coplanar
    # faces against the underside of the rim.
    pocket = cq.Workplane(obj=pocket).translate(
        (0, 0, (RIM_BOTTOM_Z - 1) - (RIM_BOTTOM_Z + RIM_THICKNESS / 2))
    )

    screen = unhollowed.cut(pocket)

    # What the hollow took out: its footprint is the span inside the rim, and so
    # the footprint of the screen that roofs it -- the face to split on.
    cavity = unhollowed.cut(screen)

    # Break the leading edges so the part finds the gap on the way in.
    screen = (
        screen.faces("<Z")
        .edges(BottomEdgesAtRadii([SCREEN_OR, SCREEN_IR], RIM_BOTTOM_Z))
        .chamfer(CHAMFER)
    )

    # The lip, in the shape the lid published when it cut its own rebate. It is
    # the whole void outline grown, not just the inner and outer arcs, so it
    # carries on round the ends and over the spokes. Sunk into the rebate rather
    # than sitting on the face, so the top finishes flush with the lid.
    screen = screen.union(lid_variant.LIP)

    return screen, cavity, pieces


def split_bodies(screen, cavity):
    """Split the screen on the roof of the hollow, into two solids.

    Both go in one STEP so they import as parts of a single object and stay
    registered to each other. The point is to give them different print
    settings: the plate spanning the hollow is the one meant to be run with no
    top or bottom layers, so its infill pattern is left exposed and becomes the
    screen mesh. Everything holding it -- the four walls and the lip -- has to
    stay solid, and is the other body.

    The split face is the roof of the cavity, so the cavity's own footprint
    defines it. Taken as a prism off the cavity rather than rebuilt from radii,
    because the footprint follows the spoke ends and root fillets too.
    """
    outline = lid_mod.section_outline(cavity, (RIM_BOTTOM_Z + SCREEN_BOTTOM_Z) / 2)
    prism = cq.Solid.extrudeLinear(outline, [], cq.Vector(0, 0, 3 * TOP_Z))
    prism = cq.Workplane(obj=prism).translate((0, 0, -TOP_Z))

    return screen.cut(prism), screen.intersect(prism)


screen, cavity, pieces = build_screen()
solid_body, infill_body = split_bodies(screen, cavity)

if __name__ == "__main__":
    show_object(
        lid_variant.lid,
        name="led_sun_lid_two_spoke",
        options={"color": lid_variant.LID_COLOR, "alpha": lid_variant.ALPHA},
        clear=True,
    )
    show_object(
        lid_variant.ring_light,
        name="led_ring_light",
        options={"color": lid_variant.RING_COLOR, "alpha": lid_variant.ALPHA},
    )
    show_object(
        solid_body,
        name="lid_screen_solid",
        options={"color": SCREEN_COLOR, "alpha": ALPHA},
    )
    show_object(
        infill_body,
        name="lid_screen_infill",
        options={"color": INFILL_COLOR, "alpha": ALPHA},
    )

    dx, dy, dz = print_volume.extents(screen)
    print(f"screen: {dx:.2f} x {dy:.2f} x {dz:.2f} mm, "
          f"{screen.val().Volume() / 1000:.1f} cm3 total")
    for name, body in (("solid ", solid_body), ("infill", infill_body)):
        print(f"  {name}: {len(body.val().Solids())} solid, "
              f"{body.val().Volume() / 1000:.1f} cm3")

    if print_volume.fits(screen):
        # Both bodies in one file, for importing as parts of a single object --
        # they arrive already registered to each other. The same two bodies go
        # out separately as well, for adding one to the other by hand.
        both = cq.Compound.makeCompound([solid_body.val(), infill_body.val()])
        exports = {
            "lid_screen.step": cq.Workplane(obj=both),
            "lid_screen_solid.step": solid_body,
            "lid_screen_infill.step": infill_body,
        }
        for filename, body in exports.items():
            cq.exporters.export(body, str(OUTPUT_DIR / filename))
            print(f"  wrote {filename}")
    else:
        print("NOT exported: does not fit the build volume.")
