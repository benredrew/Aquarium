<!--
Author: Claude (Sonnet 5)
Co-Author: Brendan Fennell
-->
# Print Log — Tube Test Fits

Record of `test_fits/tube.py` exports that were actually printed and tested against the vessel. Only confirmed prints belong here — see notes below for exports that were generated but skipped.

| Date | Time (approx) | OD (mm) | Wall (mm) | Height (mm) | ID (mm) | Notes | Feedback |
|------|----------------|---------|-----------|--------------|---------|-------|----------|
| 2026-08-01 | 16:23 | 180 | 2 | 10 | 176 | First export, initial baseline dimensions | |
| 2026-08-01 | 16:26 | 180 | 2 | 10 | 176 | Re-export after wiring up the live viewer (`set_port` fix); same dimensions as above | |
| 2026-08-01 | 16:33 | 180 | 2 | 10 | 176 | Re-export after relocating script into `test_fits/` folder structure; same dimensions as above | |
| 2026-08-01 | 17:40 | 168 | 2 | 10 | 164 | OD reduced from 180 to 168 (via intermediate 170/166mm trials at 5mm height, not logged here since not printed at that height) | |

## Notes

- Exports at OD 169mm and OD 167mm (both 2mm wall, 10mm height, ~18:23–18:24 on 2026-08-01) were generated but **not printed** — omitted from this log by request.
- This log only tracks the `tube.py` test-fit part. Confirmed vessel measurements (not test-fit trial values) belong in `DIMENSIONS.md`.
- Since `test_fits/output/*.step` is gitignored and overwritten on every run, this log is the only durable record of what dimensions were actually exported and tested — update it whenever a print is confirmed.
