# Aquarium

CadQuery models for the aquarium lid, LED ring reference, and test-fit parts,
plus the workshop jigs built to make them.

## Omarchy viewer

Open **OCPViewer** from the application launcher, or run `./viewer`.
The viewer opens in its own app-style window without choosing or loading an assembly.
Tools and Info start collapsed; click their toggles to expand them.
The service runs `cad-python -m cadkit.viewer --server`, which applies these
startup defaults. They live in the shared `cadkit` package rather than here,
so every CAD project on this machine opens the same unobtrusive window.
The local OCP viewer runs on `127.0.0.1:3939` as the user service
`aquarium-viewer.service`, started on demand.

To load the aquarium assembly, or update it after editing a model, run:

```bash
./preview
```

The assembly preview does not export files. Run individual part scripts to
produce their STEP exports, for example `./preview led_sun_lid/lid.py`.
The wrapper uses a project-local font configuration compatible with the CAD
library on Linux; Arial falls back to Liberation Sans for engraving.

Dependencies are installed in `.venv` using Python 3.12; direct dependencies
are in `requirements.txt` and the complete installed versions in
`requirements-lock.txt`. The desktop entry and systemd service are local
machine setup, outside this repository.

To stop the viewer server: `systemctl --user stop aquarium-viewer.service`.
To inspect logs: `journalctl --user -u aquarium-viewer.service`.

## Workshop parts

`saw_block/` is not aquarium hardware — it is a mitre block for square hand-sawn
cuts, cut to the hacksaw in `spec/hacksaw.md` and the stock in `spec/lumber.md`.
It lives here because it reads the same `spec/` documents and the same build
volume as everything else. It prints in two pieces:

```bash
./preview saw_block/block.py
```

- `saw_block.step` — the block, as modelled: floor down, no supports.
- `saw_block_cleat.step` — the bench-hook cleat, lip down, as it is used.

The cleat slides into a dovetail along the underside and wants a mallet tap, not
a push. Neither part needs supports.
