---
type: Report
description: "W-250 DoD 2 - the fux merge driver exercised on a scratch clone of the fux repository: two branches each edit and re-ingest one document in the same shard, then merge. The shard merged with no hand edit. The REGISTER merge silently kept a stale sha for the other side's document; it was fixed in the same change (three-way on loc), and on the re-run the merged index equals a fresh ingest except for git-derived mtime."
run: 2026-10-09-merge-driver-dogfood
item: W-250
classification: informed
filed: 2026-10-09
---

# Report: the merge driver, run on its own repository

**No pre-registration**: a surface capture with no threshold and no verdict. It
answers W-250 DoD 2: *two branches each re-ingest, merge, and the index resolves
without a hand edit.* `informed`; no golden path is read, and a `git clone` carries
no gitignored file.

**Setup** ([`evidence/merge_exercise.sh`](evidence/merge_exercise.sh)): a `git
clone` of this repository at `59f8a807` into the session scratchpad, with
`.venv/bin` first on `PATH`. In the clone: `fux hooks`, then `fux ingest --no-fetch`,
then a commit as the base. Branch A appends one line to
`work/compare/section-units.compare.md`; branch B appends one line to
`work/regression/2026-08-24-rerank-and-goldens/ANALYSIS.md`. Both documents hash
into shard `00.jsonl`. Each branch re-ingests and commits. Then side A is merged
into side B. Ingest is `--no-fetch`, because the repository's URL sources made the
first attempt wait on the network. Each re-ingest took about 33 s; the base took
2 m 20 s.

| attempt | what happened | evidence |
|---|---|---|
| 0 | **The driver was never invoked.** The base commit staged `.fux/` only, so `.gitattributes` reached side A's commit and not side B's. git reads merge attributes from the branch being merged **into**, so `00.jsonl` merged textually: one conflict, on adjacent lines. A setup slip in the exercise, kept because the same thing happens to any branch forked before `.gitattributes` gained the lines | [log](evidence/attempt-0-attributes-on-one-side.log) |
| 1 | `.gitattributes` committed in the base. **Merge clean, no hand edit, no markers.** `00.jsonl` carries both sides' records. ⚠ **`REGISTER` kept side B's stale sha for side A's document** (base `29690fe1` → A `7bfed6c2`; merged `29690fe1`). `_merge_register` was a union in which ours won every `loc` and the ancestor was never consulted | [log](evidence/attempt-1-register-defect.log) |
| 2 | **Driver fixed** (three-way on `loc`, decision 4 per row); same script. **Merge clean, no hand edit.** A fresh `fux ingest` of the merged tree differs from the merge commit in **`mtime` only**, on the two edited records | [log](evidence/attempt-2-fixed-driver.log) |

**The `mtime` difference is not the merge's.** `mtime` is git's time for the
file ([SR-INDEX-RECORD](../../../records/0109_index-record.md)), and each side
ingested *before* committing its edit. The first ingest after any such commit
moves it, merged or not.

**What it changed:** [SR-MERGE-DRIVER](../../../records/0130_merge-driver.md)'s
register bullet and its Consequences, `src/fux/maintain/mergedriver.py`, and five
register tests in `tests/maintain/test_mergedriver.py`. Two of those tests fail
on the old driver. ⚠ The installed hooks were live in the clone: post-commit spawned
a background re-index after each commit, and post-merge stopped it and ran its
own ingest (*"stopped the background re-index"* in the logs). Whether a runner
overlapped a script ingest was not isolated. The result does not depend on it,
because each branch's committed index was read from git, not from the working
tree.

**Not shown:** an add/add of a shard file (git never calls the driver for one,
per the record's Consequences), a merge with both sides editing one document,
Windows.
