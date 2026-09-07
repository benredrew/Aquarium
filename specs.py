# Author: Claude (Opus 5)
# Co-Author: Brendan Fennell
"""The specification documents in spec/, read as numbers.

spec/ holds one document per off-the-shelf component -- what the thing is -- plus
fits.md, which holds the allowances to leave between things. They are written for
a person to read; this module lets the scripts read them too, so a figure exists
in exactly one place. The document says the vessel base is 178mm, so the vessel
model is 178mm and the cradle cut to take it follows, with no second copy to
forget.

Documents are addressed by filename stem, figures by key:

    specs.figure("vessel", "top_opening_id")
    specs.figure("fits", "free_wall_radial")

Naming a document as well as a key keeps two components free to use the same word
for their own dimension without colliding.

## What is readable

Only a table whose first column is `Key`. A table without one is prose for people
and is left alone -- which is how a document can carry both, and how a row can be
excluded simply by leaving its key off.

A row describes a thing and each of its `(mm)` columns describes one dimension of
it, so a figure is named for both: row `top_opening` under column `ID (mm)` is
`top_opening_id`. That way one row carries a section's OD, wall, ID and height
without the table needing a line per number.

The exception is a column headed exactly `Value (mm)`, which contributes nothing
to the name -- row `free_wall_radial` there is just `free_wall_radial`. Tables
that put one figure per row read better that way, and would otherwise all come
out as `..._value`.

## Failure

A missing document, an unknown key, or a `(mm)` cell that is not a number raises.
Nothing falls back on a default: a part quietly built to the wrong diameter is
worse than one that refuses to build at all.
"""
import re
from pathlib import Path

SPEC_DIR = Path(__file__).parent / "spec"

# A markdown row, split on the pipes, with the outer empties dropped.
_ROW = re.compile(r"^\s*\|(.+)\|\s*$")
# The key cell: a single `backticked` identifier and nothing else.
_KEY = re.compile(r"^`([a-z0-9_]+)`$")
# Only columns declaring their unit hold figures; the rest are prose.
_MM = re.compile(r"\(\s*mm\s*\)\s*$", re.I)
_NOTE_COLUMNS = ("notes", "history")
# A column that names no dimension of its own; the row key stands alone.
_ANONYMOUS = "value"


def _slug(header):
    """`Corner radius (mm)` -> `corner_radius`."""
    return re.sub(r"[^a-z0-9]+", "_", _MM.sub("", header).strip().lower()).strip("_")


def _parse(text, where):
    """Every figure in every keyed table of one document, {name: (mm, note)}."""
    figures = {}
    headers = None  # the keyed table currently being read, if any
    note_at = None
    for line in text.splitlines():
        row = _ROW.match(line)
        if not row:
            headers = None  # a blank line or prose ends the table
            continue
        cells = [cell.strip() for cell in row.group(1).split("|")]
        if cells[0].lower() == "key":
            headers = cells
            note_at = next(
                (i for i, h in enumerate(cells) if h.lower() in _NOTE_COLUMNS), None
            )
            continue
        key = _KEY.match(cells[0]) if headers else None
        if not key:
            continue  # separator, an unkeyed table, or a row without a key
        note = cells[note_at] if note_at is not None and note_at < len(cells) else ""
        for i, header in enumerate(headers[1:], start=1):
            if not _MM.search(header) or i >= len(cells) or not cells[i]:
                continue  # a prose column, or this row leaves it blank
            column = _slug(header)
            name = key.group(1) if column == _ANONYMOUS else f"{key.group(1)}_{column}"
            try:
                figures[name] = (float(cells[i]), note)
            except ValueError as exc:
                raise ValueError(
                    f"{where}: figure `{name}` reads {cells[i]!r}; a column headed "
                    f"{header!r} must hold millimetres alone."
                ) from exc
    return figures


_DOCUMENTS = {
    path.stem: _parse(path.read_text(encoding="utf-8"), path.name)
    for path in sorted(SPEC_DIR.glob("*.md"))
}


def _row(document, key):
    try:
        figures = _DOCUMENTS[document]
    except KeyError:
        raise KeyError(
            f"no spec/{document}.md; the folder has {sorted(_DOCUMENTS)}."
        ) from None
    try:
        return figures[key]
    except KeyError:
        raise KeyError(
            f"{key!r} is not a keyed figure in spec/{document}.md; "
            f"it has {sorted(figures)}."
        ) from None


def figure(document, key):
    """The value in mm of `key` in spec/`document`.md."""
    return _row(document, key)[0]


def note(document, key):
    """The Notes/History cell behind `key` -- where the figure came from."""
    return _row(document, key)[1]


if __name__ == "__main__":
    import sys

    # The note cells are prose and carry punctuation like arrows, which a cp1252
    # console refuses outright. The parse is UTF-8 throughout; only this dump has
    # to survive whatever the terminal happens to be set to.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for document in sorted(_DOCUMENTS):
        print(f"spec/{document}.md")
        if not _DOCUMENTS[document]:
            print("    (no keyed tables)")
        for name in sorted(_DOCUMENTS[document]):
            print(f"    {name:24s} = {figure(document, name):9.4f} mm")
