# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""Aquarium's engraver -- now `cadkit.engrave`, re-exported here.

Labelling a part with the dimension it controls is not specific to this
project, and `fitkit` became the second consumer, so the implementation moved
to the shared package. This module stays as a re-export because fifteen files
here import it by name; changing all fifteen to prove a point would risk far
more than it gains, and the one thing that must never happen to this module is
a second copy of it -- a duplicated font lookup broke six parts on 2026-09-27.

New code should `from cadkit import engrave`.
"""
from cadkit.engrave import *          # noqa: F401,F403
from cadkit.engrave import (          # noqa: F401  -- names not covered by *
    ENGRAVE_DEPTH,
    FONT_CANDIDATES,
    FONT_PATH,
    FONT_SIZE,
    OVERSHOOT,
    TRACKING,
    WIDTH_SCALE,
    engrave_radial_text,
    labelled_ring,
)
