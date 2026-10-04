---
type: Verdict
name: W-252-NODE-ARM
description: "W-252: PASS on the frozen endpoint on both rungs, 0 discordant of 801 on every pass, identical graph digests, and a Node-built plane byte-equal to Python's. The build check was re-run once with a corrected procedure (it had deleted six ingest-side files); disclosed below."
verdict: PASS
prediction: W-252-NODE-ARM
pre_registration: work/regression/2026-10-04-node-arm-2/PRE-REGISTRATION.md
run: 2026-10-04-node-arm-2
item: W-252
filed: 2026-10-04
classification: informed
---

# VERDICT: PASS. The Node arm is green on lab rungs

Against the frozen §7 endpoint, per rung:

| rung | contract | transcription | graph digest | build (files Node writes) | source rung vs manifest | copy documents vs manifest |
|---|---|---|---|---|---|---|
| rung-01000 | 0 / 801 | 0 / 801 | IDENTICAL | 602 / 602 byte-equal (re-run) | `[]` | 0 missing, 0 drifted |
| rung-10000 | 0 / 801 | 0 / 801 | IDENTICAL | 602 / 602 byte-equal (re-run) | `[]` | 0 missing, 0 drifted |

**The build row, and a procedure defect disclosed.** As first run, §5's
command deleted the whole Python runtime directory before Node built, so
`diff -rq` also listed six ingest-side files Node's build never writes
(`decoder-digests.json`, `extract-config-digest`, `ingest-log.jsonl`,
`last-cited.json`, `pii-counts.json`, `pii-digest`) and §7's clause, read
literally, did not hold — an artifact of the procedure, not of either builder.
**The check was re-run once by the orchestrating session (Opus 5.5), deleting
only the 596 files Node's build writes**: on both rungs the two runtime
directories hold the same 602 files and **none differs, `stamp.json`
included** (the copy kept the shards' mtimes) — §7's clause met as written
([`evidence/build-diff-rerun.txt`](evidence/build-diff-rerun.txt)). No
threshold moved and the pre-registration was not edited; what changed is the
deletion step, stated here. The first run's output stays in `evidence/`.

`informed`: same model family built both readers. The endpoint is parity.
