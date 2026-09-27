<!--
Author: Claude (Opus 5)
Co-Author: Brendan Fennell
-->
# Working in this repository

For any agent — Claude, Codex, or otherwise. `CLAUDE.md` points here so there
is one copy of this rather than two that drift apart.

CadQuery models of aquarium and workshop parts, built to fit real objects.
Python 3.12 in `.venv`. Run a part with `./preview <path>`, which sets the font
configuration the engraver needs; `./preview` alone loads the assembly.

## Numbers come from `spec/`, never from your head

`spec/` holds one document per off-the-shelf component — what the thing *is* —
plus `fits.md`, the allowances to leave between things. `specs.py` reads their
tables, addressed by document and key together:

```python
specs.figure("vessel", "top_opening_id")     # 167.0
specs.figure("fits", "ring_light_bore_radial")
```

Read the figure; do not retype it. A part that hardcodes 167 is a part that
will not follow when the document changes, and `specs.figure` raises on an
unknown key rather than falling back to a default — a part built to the wrong
diameter is worse than one that refuses to build.

**A figure is only promoted into `spec/` once a printed part confirms it.**
Until then it stays a literal in the script dialling it in, and the evidence
goes in `PRINT_LOG.md`. Do not promote a figure because it seems right, and do
not fill in a Confirmed date you did not witness.

## Viewing and drawings: the shared `cadkit` package

Neither lives in this repository. Both are in `~/Projects/cadkit`, shared with
the other CAD projects -- see `~/Projects/cadkit/AGENTS.md`.

**They are optional, and must stay that way.** Building a part may not require
a viewer to be running or a sheet to be drawn; a plain rebuild is the cheap
headless thing done constantly, and taxing it with a GUI or with seconds of
hidden-line projection is what makes agent work expensive.
`lamp_shade/shade.py` is the reference:

```bash
./preview lamp_shade/shade.py              # build + STEP. No viewer needed.
./preview lamp_shade/shade.py --sheet      # ... and draw the sheet
./preview lamp_shade/shade.py --no-show    # ... and do not even look for a viewer
```

```python
from cadkit import sheet as cad_sheet, viewer as cad_viewer
cad_viewer.show(solid, name="part")      # returns False if none; never raises
cad_sheet.sheet(solid, "output/<part>_sheet.svg", "PART NAME", fields=[...])
```

Four views to one common scale — FRONT, SECTION A-A top right, PLAN,
ISOMETRIC — third angle, section hatched from the solid's real cut faces.
Call it from the part script's `__main__` so the drawing regenerates from the
same solid that gets exported and cannot drift from the part.

Two things to know before you reach for something else:

- **Do not use `cq.exporters.export(..., "SVG")` for views.** It builds its
  projection with the two-argument `gp_Ax2`, which lets OCCT invent the X
  axis, so the roll of each view is arbitrary — elevations come out on their
  side and isometrics upside down. Rotating the output afterwards is guesswork
  that has to be redone per part. `cadkit.sheet` takes a view direction *and* an
  up vector and orients the shape before projecting.
- **Sheets are dark on screen and light on paper.** The dark palette rides on
  presentation attributes; a `@media print` block carries the light one and
  wins, so a browser printing the SVG swaps to black-on-white while
  `rsvg-convert` keeps the dark version. The PNG beside the SVG is a screen
  artefact and really is dark — **print the SVG, not the PNG.**

`output/` directories are gitignored and rewritten on every run. Nothing in
them is a source file; never hand-edit one.

## The 3D viewer is shared — run your own

`aquarium-viewer.service` listens on **127.0.0.1:3939**, and every session on
this machine pushes to it. Two agents working at once silently overwrite each
other's scene, and you will screenshot someone else's model believing it is
yours. Start your own on a genuinely free port -- 3939 is this service and
3940/3941 are Oil_Shelf's. `cadkit` knows which are spoken for:

```bash
cad-python -m cadkit.viewer --status    # who is up
cad-python -m cadkit.viewer             # start one on a free port
```

It prints `CAD_VIEWER_PORT=<n>`; export that and `cad_viewer.show` uses it.
Kill it when you are done.

## You are not alone in this working tree

Several agent sessions edit this repository at the same time, in one shared
checkout. Consequences worth internalising:

- **Never `git add -A` or `git commit -a`.** Stage your own paths by name. A
  sweep captures another session's half-finished work under your message.
- `git status` shows their edits alongside yours. Files you did not touch that
  appear modified are theirs; leave them.
- **Do not switch branches.** The checkout is shared, so `git switch` moves the
  tree for every other session mid-edit. Commit on the current branch, or wait.
- `user.name` is unset in git config; `user.email` is set. Commits need
  `GIT_AUTHOR_NAME=benredrew GIT_COMMITTER_NAME=benredrew`, matching every
  existing commit, unless Brendan sets the config.
- Hyprland window IDs go stale fast while other sessions rearrange the desktop.
  Re-query `hyprctl clients -j` immediately before acting, and check what you
  acted on afterwards.

## House style

Modules carry an `Author:`/`Co-Author:` header and a docstring that explains
*why* the part is shaped as it is — what drives what, which figures are
confirmed, what was tried and reverted. Comments record decisions and their
reasons, including corrections, so the next reader does not re-litigate them.
Match it.
