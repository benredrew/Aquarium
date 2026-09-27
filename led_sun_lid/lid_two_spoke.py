# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""LED Sun Lid, two-spoke variant -- the hub and its ring light fly.

Same geometry as lid.py in every other respect: same rim, same hub bore, same
retaining lip, same cable passthrough profile, same breaks. What changes is
which spokes are present and which way the cable faces.

The cable leaves at -Y. The two spokes straddle it, sitting half a pitch either
side, so the cable exits into open water between them rather than fouling a
spoke. Pitch comes from a notional SPOKE_COUNT_THEORETICAL set of evenly spaced
spokes -- only two are built, but they sit where two of that set would.

That leaves the remaining arc open, so the hub is a cantilever: it hangs off a
short arc of rim rather than being carried across a diameter. Everything else
is imported from lid.py rather than restated, so the proven interface
dimensions cannot drift between the two versions.
"""
import importlib.util
from pathlib import Path

import cadquery as cq
from cadkit.viewer import show as show_object

OUTPUT_DIR = Path(__file__).parent / "output"

# --- Design parameters ----------------------------------------------------
# The cable faces -Y. Spokes straddle it symmetrically.
PASSTHROUGH_ANGLE = 270.0
SPOKE_COUNT_THEORETICAL = 12  # sets the pitch; only two spokes are built
SPOKE_PITCH = 360.0 / SPOKE_COUNT_THEORETICAL  # 30.0
SPOKE_ANGLES = [
    PASSTHROUGH_ANGLE - SPOKE_PITCH / 2,  # 255.0
    PASSTHROUGH_ANGLE + SPOKE_PITCH / 2,  # 285.0
]

LID_COLOR = (255, 165, 0)
RING_COLOR = (0, 170, 70)
ALPHA = 1.0  # solid


def load_part(relative_path, name):
    """Import a part script for its geometry only (no viewer/export)."""
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).resolve().parent.parent / relative_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lid_mod = load_part("led_sun_lid/lid.py", "lid")
ring_mod = load_part("led_ring_light/ring_light.py", "ring_light")

lid_plain = lid_mod.build_lid(SPOKE_ANGLES, PASSTHROUGH_ANGLE)

# --- Screen rebate --------------------------------------------------------
# The screen hangs on a lip let into the top face. Both the lip and the rebate
# that receives it are generated here, from the shape of the void itself, so the
# two are the same shape by construction and the screen has nothing to guess at.
#
# The void is taken as a prism -- the lid's vertical silhouette subtracted from
# the annulus between hub and rim -- and then simply grown. Growing it by
# SCREEN_LIP_WIDTH gives the rebate, and by SCREEN_LIP_WIDTH minus the clearance
# gives the lip, which is what leaves the gap on the walls. Because it is the
# whole void outline being grown, and not just its inner and outer arcs, the lip
# carries on round the ends and over the spokes rather than stopping short.

SWEEP = lid_mod.sweep_prism(lid_plain)
# Tall enough that the offset's rounding at the top and bottom stays clear of
# the band the rebate is taken from.
VOID_HEIGHT = lid_mod.THICKNESS + 2 * lid_mod.SCREEN_LIP_WIDTH


def void_prism():
    """The open water between hub and rim, as a prism. Long arc only."""
    blank = (
        cq.Workplane("XY")
        .circle(lid_mod.RIM_IR)
        .circle(lid_mod.HUB_OR)
        .extrude(VOID_HEIGHT)
    )
    remainder = blank.cut(SWEEP)
    # The spokes split it in two; the short piece is the cable gap.
    pieces = sorted(remainder.val().Solids(), key=lambda s: s.Volume(), reverse=True)
    return cq.Workplane(obj=pieces[0])


VOID = void_prism()


def flange(grow):
    """The void grown by `grow`, cut down to the rebate's band of the lid."""
    band = (
        cq.Workplane("XY")
        .circle(lid_mod.OUTER_R + 10)
        .extrude(lid_mod.SCREEN_LIP_DEPTH)
        .translate((0, 0, lid_mod.THICKNESS - lid_mod.SCREEN_LIP_DEPTH))
    )
    return lid_mod.offset_solid(VOID, grow).intersect(band)


# What the screen builds its lip to, and what the lid gives up to receive it.
LIP = flange(lid_mod.SCREEN_LIP_WIDTH - lid_mod.SCREEN_CLEARANCE)
REBATE = flange(lid_mod.SCREEN_LIP_WIDTH)

REBATE_FLOOR_Z = lid_mod.THICKNESS - lid_mod.SCREEN_LIP_DEPTH


def rebate_chamfer_cutter():
    """Break on the lower edge of the rebate, at the mouth of the void proper.

    Lofted between the void outline and the void grown by the chamfer rather
    than selected with Workplane.chamfer. The edge runs round the whole void --
    two arcs, two spoke ends and four root fillets -- and picking it out means
    telling it from the rebate's outer edge, which sits on the same floor face
    at the same height. The loft states the wedge directly and needs no
    selection at all.
    """
    chamfer = lid_mod.SCREEN_REBATE_CHAMFER
    lower = lid_mod.section_outline(VOID, REBATE_FLOOR_Z - chamfer)
    upper = lid_mod.section_outline(
        lid_mod.offset_solid(VOID, chamfer), REBATE_FLOOR_Z
    )
    return cq.Workplane(obj=cq.Solid.makeLoft([lower, upper]))


lid = lid_plain.cut(REBATE).cut(rebate_chamfer_cutter())

# The light drops into the hub bore from above and rests on the retaining lip.
# Its gland is modelled protruding along +Y, so the light has to be installed
# turned to point its cable at the passthrough -- rotated by the same amount the
# pocket was. Left at +Y it fouls the hub wall by 108mm^3, since there is no
# pocket there any more.
ring_light = ring_mod.ring_light.rotate(
    (0, 0, 0), (0, 0, 1), PASSTHROUGH_ANGLE - 90.0
).translate((0, 0, lid_mod.LIP_HEIGHT))

if __name__ == "__main__":
    show_object(
        lid,
        name="led_sun_lid_two_spoke",
        options={"color": LID_COLOR, "alpha": ALPHA},
        clear=True,
    )
    show_object(
        ring_light,
        name="led_ring_light",
        options={"color": RING_COLOR, "alpha": ALPHA},
    )
    cq.exporters.export(lid, str(OUTPUT_DIR / "led_sun_lid_two_spoke.step"))
