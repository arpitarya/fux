# `capture-driver/` — the template a measured run copies (W-281)

Copy this directory into the next run's `evidence/` (and the ladder driver into
the next ladder run's `evidence/`); do not edit a filed run's copy. Drivers are
unfrozen by design; the gates (`g0.py`, `g3.py`, `g4.py`, `latency.py`,
`decide.py`) are hashed in the pre-registration and are **never** copied here or
edited. Schedule changes only: no bar, gate or engine moves.

| file | what | W-281 DoD |
|---|---|---|
| `build_from_worktree.py` | gen-6's ladder driver + every builder `git commit` runs `-c commit.gpgsign=false` (fux-lab's builder unmodified) | 1 |
| `make_golden_ext_gen4.py` | the pair-ordered authored list the driver substitutes (unchanged from gen 6) | - |
| `capture.sh` | W-278's capture with G1 in the background, G3 per arm in parallel, latency last and alone, per-step wall time in `capture-timing.tsv` | 2, 3, 4, 5 |
| `g3_one_arm.py` | runs the frozen `g3.py` for one treatment arm (imports it unchanged, narrows `TREATMENTS`) and merges the per-arm reports | 3 |

Set the run-specific lines at the top of `capture.sh` (`RUNDIR`, `SET`, `SETID`,
`PFX`, `TREATMENTS`) and adapt steps 4-5 to the run's arms. Per-arm G3 reports
are filed beside the merged `g3.json`. The latency step still records `uptime`
before and after and refuses to start while a background job is alive.

DoD 5 (a measured capture of at most 30 min) is **owed by the next run**: the
timing file it writes is the proof.
