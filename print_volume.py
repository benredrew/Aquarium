# Author: Claude (Sonnet 5)
# Co-Author: Brendan Fennell
"""The printer's build volume, as a reference solid for previews.

Original Prusa MINI / MINI+, 180 x 180 x 180 mm. This is the binding constraint
on the aquarium parts -- the vessel is 180mm OD, so anything that wraps around
it has to be segmented. Showing the volume alongside a model makes that visible
rather than something to remember.

Preview only: the build volume is never exported, and `fits` exists so parts
that fall outside it are not exported either.
"""
import cadquery as cq
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

BED_X = 180.0
BED_Y = 180.0
BED_Z = 180.0

COLOR = (0, 128, 128)  # teal blue
ALPHA = 0.2  # 80% transparent

# Centred on the origin in X and Y, sitting on z=0, so it lines up with parts
# modelled about the vessel axis.
volume = cq.Workplane("XY").box(BED_X, BED_Y, BED_Z, centered=(True, True, False))


def extents(shape):
    """(dx, dy, dz) of `shape`, measured off the exact geometry.

    Uses BRepBndLib.AddOptimal rather than Shape.BoundingBox(). The plain
    bounding box reuses whatever triangulation the shape already carries, so
    the answer depends on whether the part has been rendered yet: this ring
    measured 180.00 before being shown and 180.30 after, because show_object
    meshed it and the mesh is coarser than the surface. AddOptimal works from
    the geometry and gives the same tight answer either way.

    Measuring from vertices instead is also wrong here: on a curved part the
    widest point of an arc is not a vertex, so vertices under-report.
    """
    box = Bnd_Box()
    # useTriangulation=False is the whole point -- left at its default of True
    # this still measures the mesh when one is present, and inflates the answer
    # by the triangulation deflection plus the face tolerance.
    BRepBndLib.AddOptimal_s(shape.val().wrapped, box, False, False)
    xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    return xmax - xmin, ymax - ymin, zmax - zmin


# A part clipped exactly to the build volume measures 2e-7mm over it -- boolean
# round-off, not size. Tolerance is well under one layer height, so it cannot
# admit a part that is meaningfully oversize.
FIT_TOL = 0.01


def fits(shape):
    """True if `shape` fits the build volume in its current orientation."""
    dx, dy, dz = extents(shape)
    return dx <= BED_X + FIT_TOL and dy <= BED_Y + FIT_TOL and dz <= BED_Z + FIT_TOL


def show(show_object, name="build_volume"):
    """Add the build volume to the current viewer scene."""
    show_object(volume, name=name, options={"color": COLOR, "alpha": ALPHA})
