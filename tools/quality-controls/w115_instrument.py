#!/usr/bin/env python3
"""W-115 — the instrument that can finally see the chunking change.

## Why three corpora could not, and what was actually wrong

W-115 shipped four changes and has been **unmeasured for quality** since
2026-09-06. Three corpora have been pointed at it and all three returned zero:

| corpus | grades? | headroom? |
|---|---|---|
| fux-playground | yes | none — the arms produce a byte-identical index |
| fux's own repo | no goldens | yes — 304 of 954 documents moved |
| the golden ladder | yes (phase 5) | none — **0 of 994** |

🔴 **The ladder run's diagnosis was `the ladder carries .md, .txt, .yaml, .eml
and .html — not one of the formats W-115 touches`. That sentence is wrong, and
this tool exists because re-deriving it changed the fix.**

`git diff 94231b2 676e973 -- src/fux/ingest/extract.py` says the opposite:
`.rst`, `.adoc` and `.org` already had their own regexes **before** W-115 and
were **not changed by it**. What W-115 changed for ranking is:

1. **Markdown's heading grammar became fence-aware** — and Markdown is the
   default for *every* extension without its own pattern, `.txt` and every
   decoded document included. A `# Rotate the keys` line inside a ```bash block
   used to be mined as a heading, weighted `bm25f.heading` (3.0 shipped),
   published in `phrases`, and **removed from the body**.
2. **A key stops being a heading below depth 2** (`decode/json.py::_label`,
   shared by `jsonl`, `xml`, `yaml`). Every key at every depth used to be one.

**So the ladder has the right formats and the wrong CONTENT.** Measured on
`rung-01000`: of 800 `.md`/`.txt` documents **1** carries a `#` line inside a
code fence, and of 146 `.yaml` documents **2** nest deeper than two levels. A
corpus cannot show you a change it never triggers — SR-RS decision 23b, which
calls that a data defect and not a null.

## What this corpus does differently

Every probe is a **pair**, and the pair is the whole design:

- a **subject** document, genuinely about topic `T`: `T` is its title, its
  headings and its prose;
- a **decoy** document about something else, whose only connection to `T` is an
  **incidental fenced shell comment** (`# T ...`) or a **fifth-level config
  key**.

**Ground truth is the subject, and it is not circular.** It is declared from
what the document is *about*, which is what any annotator would say and what the
reader wants; a shell comment inside a code block does not make a runbook a
document about that phrase. The W-115 change is the claim that the engine should
agree, and this measures whether it does.

⚠ **`--selftest` is the headroom proof (SR-RS decision 22c(b)).** It asserts
the two arms disagree about the decoys' heading sets and agree about everything
else — separable only by the property under test. A run whose selftest fails is
measuring nothing and says so.

## The arms, and what they are NOT

**Both arms are HEAD**, and the `old` arm monkey-patches exactly two seams:

| seam | `old` | `new` (shipped) |
|---|---|---|
| `ingest.extract._headings_and_body` | the pre-W-115 `^#{1,6}\\s+` regex, fence-blind | `decode._markdown`, fence-aware |
| `decode.json._label` | a heading at every depth | capped at `MAX_HEADING_DEPTH` |

⚠ **This deliberately does NOT run the 94231b2 tree.** 25 files and 1 290 lines
changed between the two commits — `decode/__init__.py`, `refer/_chunk.py`,
`mail.py`, the `doc`-suffix rename, `max_phrases` 12 → 32. Checking that tree
out would measure the whole range and call it W-115, which is the confound
W-116's report had to unpick by hand. `max_phrases` is left at HEAD's default in
**both** arms, so it is not a variable here at all.

**What this therefore measures:** W-115's heading-grammar and key-depth changes,
which are its ranking half. Its `refer/_chunk.py` half is a passage-boundary
change and is not on this endpoint.

Usage:
    python3 tools/quality-controls/w115_instrument.py gen  --dest <dir>
    python3 tools/quality-controls/w115_instrument.py run  --corpus <dir> \
        --json work/regression/<run>/evidence/w115-probes.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "bin" / "python"
FUX = ROOT / ".venv" / "bin" / "fux"

sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))
from verdict import FLOOR_OF_ALL_FLOORS, line as vline, rule as vrule  # noqa: E402

SEED = 20260912

#: Probe topics are COMPOSED, not listed, for the same reason W-144's are:
#: `df` becomes the generator's choice rather than English's, and the set can be
#: widened without a hand-written list drifting out of unique.
_A = ("zol", "quen", "mar", "vin", "kel", "ori", "thal", "pyr", "bex", "cin",
      "nyq", "sper", "dro", "ash", "mor", "tel", "hav", "bren", "ors", "wick",
      "gal", "olm", "syr", "dun", "fen", "lor", "tav", "esk", "rud", "pil")
_B = ("frane", "drix", "beth", "taro", "spar", "dune", "met", "rocol", "wald",
      "drol")
#: 🔴 **Ninety topics, THIRTY probes — one disjoint slice per family, and this
#: was a defect before it was a design.** The first version reused one topic
#: across all three families, so a query for it matched the `fence` subject,
#: the `depth` subject AND the `placebo` subject at once. The three pairs
#: competed with each other, `hit@1` was 0 in both arms on two families, and the
#: whole endpoint read as Inconclusive for a reason that had nothing to do with
#: W-115. A probe that shares its query with another probe is not a probe.
TOPICS = [a + b for b in _B for a in _A][:90]
assert len(set(TOPICS)) == 90
N_PROBES = 30

#: The subjects the decoys are genuinely about, so a decoy is a real document
#: rather than a sentence with a code block stapled to it.
DECOY_SUBJECTS = [
    "certificate rotation", "log shipping", "disk pressure", "queue drain",
    "index compaction", "replica failover", "token refresh", "cache warmup",
    "backup verification", "socket tuning", "batch replay", "mirror sync",
    "quota audit", "shard rebalance", "trace sampling", "alert routing",
    "image pruning", "session eviction", "route reload", "credential vaulting",
    "snapshot pruning", "lease renewal", "digest rebuild", "watchdog restart",
    "cursor replay", "bucket lifecycle", "endpoint drain", "secret rollover",
    "journal compaction", "cluster cordon",
]
assert len(DECOY_SUBJECTS) >= N_PROBES

FILLER_TOPICS = [
    "dock scheduling", "reefer maintenance", "driver rostering", "fuel reconciliation",
    "pallet labelling", "customs paperwork", "yard marshalling", "tyre inspection",
]


def scaffold(dest: Path, types: list[str]) -> None:
    """Let `fux setup` write the repo, then declare the corpus.

    ⚠ **Hand-writing `fux.toml` was wrong and failed loudly, which is the point.**
    `[sources] dirs` stopped being a TOML key when SR-DIR-LIST landed, and a
    generator carrying its own copy of the config shape is a second source of
    truth that drifts silently. `fux setup` is the one that cannot.
    """
    # 🔴 `git init` FIRST, and it is not optional. The repo root is resolved by
    # walking up, and `~/my_programs/fux-lab/` carries its own `fux.toml` — so
    # without a root here `fux setup` silently adopts the LAB as the repo and
    # writes nothing in the corpus. It exits 0 while doing it.
    subprocess.run(["git", "init", "-q"], cwd=str(dest), check=True)
    r = subprocess.run([str(FUX), "setup", "--no-agents"], cwd=str(dest),
                       text=True, capture_output=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit("fux setup failed")
    (dest / ".fux" / "sources" / "dirs").write_text(
        "# The generated corpus. Declared, never derived (SR-DIR-LIST).\ndocs\n",
        encoding="utf-8")
    # ⚠ **No types file is written, and the argument is kept only to document
    # that.** The list moved to `.fux/formats.toml` (SR-TYPES decision 12) and
    # `setup` writes the built-in default there — which already admits every
    # format these corpora use. A second list here is refused by name, which is
    # how this was found rather than guessed at.
    assert types, "the corpus must name the formats it depends on"


# ---------------------------------------------------------------------------
# gen
# ---------------------------------------------------------------------------

#: 🔴 **The first version of these documents saturated at 30/30 in both arms,
#: and the reason is worth keeping.** The subject carried the topic in its
#: TITLE, its H1 and a dozen prose sentences, so it outranked its decoy
#: whatever the decoy's fenced comment counted as. The selftest passed — the
#: arms really did extract different headings — and the ranking still could not
#: move, which is decision 22d's Inconclusive arriving through the back door:
#: the endpoint had no headroom even though the corpus did.
#:
#: **The pair is now built so the contested field is the ONLY thing deciding.**
#: A subject is about its topic in PROSE, at a tf the caller sets; a decoy
#: mentions it `FENCE_HITS` times and only inside a code fence. Pre-W-115 those
#: fenced lines are headings at `bm25f.heading` (3.0 shipped) and are removed
#: from the body; post-W-115 they are ordinary body text at 1.0.

#: How many times a decoy names the topic inside its fence.
FENCE_HITS = 3

PROSE_FILLER = (
    "consignment despatch tolerance interval calibration schedule handover "
    "register escalation supervisor ambient variance corridor threshold "
    "inspection clearance dispatch reconciliation allocation checkpoint"
).split()


def _pad(rng: random.Random, n: int) -> str:
    words = [rng.choice(PROSE_FILLER) for _ in range(n)]
    return "\n".join(" ".join(words[i:i + 14]) + "." for i in range(0, len(words), 14))


def _subject_md(rng: random.Random, topic: str, subject: str, i: int, tf: int) -> str:
    """About `topic` in PROSE only. Its title and headings never name the topic,
    so the whole of its case is body evidence — which is the half the fence
    change does not touch."""
    hits = "\n".join(
        f"The {topic} reading is logged against the register before the shift closes."
        for _ in range(tf))
    return (
        f"---\ntitle: {subject.title()} procedure\n---\n\n"
        f"# {subject.title()} procedure\n\n"
        f"{hits}\n\n"
        f"## Detail\n\n{_pad(rng, 60)}\n\n"
        f"## Records\n\nRetained for seven years. Reference {i:04d}.\n")


def _decoy_md(rng: random.Random, topic: str, subject: str, i: int) -> str:
    """About `subject`. Its ONLY mention of `topic` is inside a code fence."""
    fence = "\n\n".join(
        f"# {topic.title()} step {k + 1}\nopsctl run --stage {k + 1}"
        for k in range(FENCE_HITS))
    return (
        f"---\ntitle: {subject.title()} runbook\n---\n\n"
        f"# {subject.title()} runbook\n\n"
        f"Run this from the operations host after the nightly window closes.\n\n"
        f"## Procedure\n\n```bash\n{fence}\n```\n\n"
        f"## Detail\n\n{_pad(rng, 60)}\n\n"
        f"## Rollback\n\nRe-run the preflight and stop. Reference {i:04d}.\n")


def _subject_yaml(rng: random.Random, topic: str, subject: str, i: int, tf: int) -> str:
    """`topic` in VALUES only — prose to every arm, never a key."""
    notes = "\n".join(f"  note_{k}: the {topic} reading is logged before handover"
                       for k in range(tf))
    return (f"{subject.replace(' ', '_')}_procedure:\n{notes}\n"
            f"  detail: {' '.join(rng.choice(PROSE_FILLER) for _ in range(30))}\n"
            f"reference: R{i:04d}\n")


def _decoy_yaml(rng: random.Random, topic: str, subject: str, i: int) -> str:
    """`topic` as a depth-5 KEY, `FENCE_HITS` times over. A heading at every
    depth in the old arm; bold body text past depth 2 in the shipped one."""
    blocks = "\n".join(
        f"    stage_{k}:\n      checks:\n        {topic}: threshold four, do not edit"
        for k in range(FENCE_HITS))
    return (f"{subject.replace(' ', '_')}_pipeline:\n  stages:\n{blocks}\n"
            f"  detail: {' '.join(rng.choice(PROSE_FILLER) for _ in range(30))}\n"
            f"reference: R{i:04d}\n")


def _filler(rng: random.Random, i: int) -> tuple[str, str]:
    t = rng.choice(FILLER_TOPICS)
    body = (
        f"---\ntitle: {t.title()} note {i:04d}\n---\n\n"
        f"# {t.title()} note {i:04d}\n\n"
        f"Routine {t} note. Nothing in this document is a procedure.\n\n"
        f"## Detail\n\n" + "\n".join(f"- {t} line {j}." for j in range(8)) + "\n"
    )
    return f"filler/{i:04d}-note.md", body


def cmd_gen(a) -> int:
    dest = Path(a.dest)
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "docs").mkdir(parents=True)
    scaffold(dest, ['.md', '.txt', '.yaml', '.json', '.jsonl', '.csv'])

    rng = random.Random(SEED)
    probes: list[dict] = []
    files: dict[str, str] = {}

    for i in range(N_PROBES):
        subject = DECOY_SUBJECTS[i]
        tf = a.tf
        slug = subject.replace(" ", "-")

        # -- family `fence`: a shell comment that looks like a heading
        topic = TOPICS[i]
        s = f"docs/{i:03d}-{slug}-procedure.md"
        d = f"docs/{i:03d}-{slug}-runbook.md"
        files[s] = _subject_md(rng, topic, subject, i, tf)
        files[d] = _decoy_md(rng, topic, subject, i)
        probes.append({"id": f"f{i:02d}", "family": "fence", "query": topic,
                       "relevant": s, "decoy": d, "subject_tf": tf,
                       "why": f"the runbook's only {topic} is a fenced shell comment"})

        # -- family `depth`: a fifth-level config key
        topic = TOPICS[N_PROBES + i]
        sy = f"docs/{i:03d}-{slug}-policy.yaml"
        dy = f"docs/{i:03d}-{slug}-pipeline.yaml"
        files[sy] = _subject_yaml(rng, topic, subject, i, tf)
        files[dy] = _decoy_yaml(rng, topic, subject, i)
        probes.append({"id": f"d{i:02d}", "family": "depth", "query": topic,
                       "relevant": sy, "decoy": dy, "subject_tf": tf,
                       "why": f"the pipeline's only {topic} is a depth-5 key"})

        # -- family `placebo`: the same shape with NO fence and NO deep key, so
        #    neither arm can differ. If it moves, the run is void.
        topic = TOPICS[2 * N_PROBES + i]
        sp = f"docs/{i:03d}-{slug}-charter.md"
        dp = f"docs/{i:03d}-{slug}-note.md"
        files[sp] = _subject_md(rng, topic, subject, i, tf)
        files[dp] = (
            f"---\ntitle: {subject.title()} note\n---\n\n"
            f"# {subject.title()} note\n\n"
            + "\n".join(f"A {topic} item was raised and closed."
                        for _ in range(FENCE_HITS))
            + f"\n\n## Detail\n\n{_pad(rng, 60)}\n")
        probes.append({"id": f"p{i:02d}", "family": "placebo", "query": topic,
                       "relevant": sp, "decoy": dp, "subject_tf": tf,
                       "why": "the decoy's mentions are plain prose — neither arm can differ"})

    for i in range(a.filler):
        rel, body = _filler(rng, i)
        files[f"docs/{rel}"] = body

    for rel, body in sorted(files.items()):
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    (dest / "probes.jsonl").write_text(
        "".join(json.dumps(p, sort_keys=True) + "\n" for p in probes), encoding="utf-8")
    print(f"{len(files)} documents, {len(probes)} probes -> {dest}")
    print(f"  fence   {sum(1 for p in probes if p['family'] == 'fence')}")
    print(f"  depth   {sum(1 for p in probes if p['family'] == 'depth')}")
    print(f"  placebo {sum(1 for p in probes if p['family'] == 'placebo')}")
    return 0


# ---------------------------------------------------------------------------
# the two arms
# ---------------------------------------------------------------------------

#: The two seams, patched identically by the arm driver and by the selftest so
#: they can never disagree about what "old" means.
#:
#: ⚠ **`_label` has to be patched on FOUR modules, not one.** `yaml`, `jsonl`
#: and `xml` each do `from fux.decode.json import _label`, so each holds its own
#: reference and rebinding `json._label` alone leaves three decoders on the
#: shipped behaviour. The first selftest did exactly that and reported 30 of 60
#: decoys separable — which is what a selftest is for.
PATCH_OLD = r"""
import re as _re

_OLD_MD = _re.compile(r"^(#{1,6})\s+(?P<text>.+?)\s*$", _re.MULTILINE)


def patch_old():
    import fux.decode.json as _J
    import fux.decode.jsonl as _JL
    import fux.decode.xml as _XM
    import fux.decode.yaml as _YA
    import fux.ingest.extract as _E

    def _old_headings_and_body(rel_path, body):
        g = _E._grammar(rel_path) or _OLD_MD
        return ([m.group("text").strip() for m in g.finditer(body)], g.sub("", body))

    def _old_label(label, depth):
        return "#" * min(depth, 6) + " " + label

    _E._headings_and_body = _old_headings_and_body
    for _m in (_J, _JL, _XM, _YA):
        _m._label = _old_label
"""

#: Run inside a fresh interpreter so the `old` arm's patches cannot leak into
#: the `new` arm through a warm module cache.
ARM_DRIVER = PATCH_OLD + r'''
import json, sys
from pathlib import Path

arm, root, probes_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

if arm == "old":
    patch_old()

from fux.cli import main

sys.argv = ["fux", "ingest", "--full"]
rc = main()
if rc != 0:
    raise SystemExit(f"ingest failed in arm {arm}: rc={rc}")
sys.argv = ["fux", "build"]
rc = main()
if rc != 0:
    raise SystemExit(f"build failed in arm {arm}: rc={rc}")

import io, contextlib
rows = []
for line in Path(probes_path).read_text().splitlines():
    if not line.strip():
        continue
    p = json.loads(line)
    buf = io.StringIO()
    sys.argv = ["fux", "ask", p["query"], "--json", "--top", "5"]
    with contextlib.redirect_stdout(buf):
        rc = main()
    try:
        res = json.loads(buf.getvalue()).get("results", [])
    except Exception:
        res = []
    locs = [r.get("loc") for r in res]
    rows.append({"arm": arm, "id": p["id"], "family": p["family"], "query": p["query"],
                 "relevant": p["relevant"], "decoy": p.get("decoy"),
                 "top": locs,
                 "hit1": bool(locs) and locs[0] == p["relevant"],
                 "decoy_at_1": bool(locs) and p.get("decoy") is not None
                               and locs[0] == p["decoy"],
                 "rank": (locs.index(p["relevant"]) + 1) if p["relevant"] in locs else 0})
Path(out_path).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
print(f"arm {arm}: {len(rows)} probes")
'''


def _run_arm(arm: str, corpus: Path, probes: Path, out: Path) -> None:
    work = corpus.parent / f"{corpus.name}-{arm}"
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(corpus, work)
    driver = work / "_arm.py"
    driver.write_text(ARM_DRIVER, encoding="utf-8")
    p = subprocess.run([str(PY), str(driver), arm, str(work), str(probes), str(out)],
                       cwd=str(work), text=True, capture_output=True, check=False)
    sys.stdout.write(p.stdout)
    if p.returncode != 0:
        sys.stderr.write(p.stderr)
        raise SystemExit(f"arm {arm} failed")


def cmd_selftest(a) -> int:
    """SR-RS 22c(b): the arms must disagree about the decoys and about nothing
    else. Asserted on extraction, in two fresh processes, before any ranking
    number exists.

    🔴 **Two processes, not two calls.** `patch_old()` rebinds module globals,
    and a decoder's output is produced inside `parse_document` — so an in-process
    "unpatch" would be a second implementation of the thing under test. Each arm
    gets its own interpreter and the parent only diffs the two dumps.
    """
    corpus = Path(a.corpus)
    probes = [json.loads(l) for l in (corpus / "probes.jsonl").read_text().splitlines()
              if l.strip()]
    rels = sorted({p["relevant"] for p in probes} | {p["decoy"] for p in probes if p["decoy"]})

    script = PATCH_OLD + r"""
import json, sys
from pathlib import Path

arm, corpus = sys.argv[1], Path(sys.argv[2])
if arm == "old":
    patch_old()

import fux.ingest.extract as E
from fux.ingest.parse import parse_document

out = {}
for rel in json.loads(sys.argv[3]):
    doc = parse_document((corpus / rel).read_bytes(), rel, corpus)
    out[rel] = None if doc is None else E._headings_and_body(rel, doc.body)[0]
print(json.dumps(out))
"""
    drv = corpus / "_selftest.py"
    drv.write_text(script, encoding="utf-8")
    dumps = {}
    for arm in ("old", "new"):
        r = subprocess.run([str(PY), str(drv), arm, str(corpus), json.dumps(rels)],
                           cwd=str(corpus), text=True, capture_output=True, check=False)
        if r.returncode != 0:
            sys.stderr.write(r.stderr)
            return 1
        dumps[arm] = json.loads(r.stdout)

    unreadable = [rel for rel in rels if dumps["new"][rel] is None]
    decoys = {p["decoy"] for p in probes if p["decoy"]}
    subjects = {p["relevant"] for p in probes}
    differs = {rel for rel in rels if dumps["old"][rel] != dumps["new"][rel]}

    d_diff = len(decoys & differs)
    s_diff = len(subjects & differs)
    print(f"documents read in both arms:                         "
          f"{len(rels) - len(unreadable)} / {len(rels)}")
    print(f"decoys whose heading set differs between the arms:    {d_diff} / {len(decoys)}")
    print(f"subjects whose heading set differs between the arms:  {s_diff} / {len(subjects)}")
    by_fam = {}
    for p in probes:
        if p["decoy"]:
            by_fam.setdefault(p["family"], [0, 0])
            by_fam[p["family"]][1] += 1
            if p["decoy"] in differs:
                by_fam[p["family"]][0] += 1
    for fam, (d, n) in sorted(by_fam.items()):
        print(f"  {fam:<8} {d} / {n}")
    # 🔴 **The placebo family must be INSEPARABLE — that is its entire job**,
    # so a blanket "every decoy differs" is the wrong assertion and said so the
    # first time it ran. Three conditions, one per role.
    treated = {f: by_fam.get(f, [0, 0]) for f in ("fence", "depth")}
    pl_d, pl_n = by_fam.get("placebo", [0, 0])
    ok = (all(d == n and n for d, n in treated.values())
          and pl_d == 0 and s_diff == 0 and not unreadable)
    print()
    if ok:
        print("SELFTEST PASSES (SR-RS 22c(b)): every TREATED decoy is separable "
              "by the property under test, no placebo decoy is, and no subject is. "
              "Headroom is PROVEN, not observed.")
    else:
        print("SELFTEST FAILS: the arms do not isolate the property under test. "
              "Any number from this corpus measures something else.")
        if s_diff:
            print(f"  {s_diff} SUBJECT documents also differ — the arms are moving "
                  f"documents the probe does not control for.")
        for fam, (d, n) in sorted(treated.items()):
            if d != n:
                print(f"  treated family `{fam}`: only {d} of {n} decoys are separable.")
        if pl_d:
            print(f"  placebo family: {pl_d} of {pl_n} decoys ARE separable, and none "
                  f"may be — the control cannot vouch for anything.")
    return 0 if ok else 1


def _both_arms(corpus: Path):
    probes_path = corpus / "probes.jsonl"
    probes = [json.loads(l) for l in probes_path.read_text().splitlines() if l.strip()]
    out = {}
    for arm in ("old", "new"):
        dest = corpus.parent / f"{corpus.name}-rows-{arm}.jsonl"
        _run_arm(arm, corpus, probes_path, dest)
        out[arm] = {json.loads(l)["id"]: json.loads(l)
                    for l in dest.read_text().splitlines() if l.strip()}
    return probes, out


def cmd_run(a) -> int:
    corpus = Path(a.corpus)
    probes, out = _both_arms(corpus)

    fams = ["fence", "depth", "placebo"]
    print()
    print(f"{'family':>9}  {'n':>4}  {'hit@1 old':>10}  {'hit@1 new':>10}  "
          f"{'decoy@1 old':>12}  {'decoy@1 new':>12}  {'discordant':>11}  {'net':>4}")
    verdicts = {}
    for fam in fams:
        ids = [p["id"] for p in probes if p["family"] == fam]
        o = sum(1 for i in ids if out["old"][i]["hit1"])
        n = sum(1 for i in ids if out["new"][i]["hit1"])
        do = sum(1 for i in ids if out["old"][i]["decoy_at_1"])
        dn = sum(1 for i in ids if out["new"][i]["decoy_at_1"])
        b = sum(1 for i in ids if out["new"][i]["hit1"] and not out["old"][i]["hit1"])
        c = sum(1 for i in ids if out["old"][i]["hit1"] and not out["new"][i]["hit1"])
        verdicts[fam] = (len(ids), o, n, do, dn, b, c)
        print(f"{fam:>9}  {len(ids):>4}  {o:>6} /{len(ids):<3}  {n:>6} /{len(ids):<3}  "
              f"{do:>12}  {dn:>12}  {b + c:>11}  {b - c:>+4}")

    print()
    for fam in ("fence", "depth"):
        nq, o, n, do, dn, b, c = verdicts[fam]
        v = vrule(b, c, better="the SHIPPED arm (W-115) ranks better",
                  worse="the PRE-W-115 arm ranks better")
        head_imp = sum(1 for p in probes if p["family"] == fam
                       and not (out["old"][p["id"]]["hit1"] and out["new"][p["id"]]["hit1"]))
        head_reg = sum(1 for p in probes if p["family"] == fam
                       and (out["old"][p["id"]]["hit1"] or out["new"][p["id"]]["hit1"]))
        print(f"[{fam}] headroom improvement {head_imp}/{nq} · regression {head_reg}/{nq} "
              f"(SR-RS 22b, PROVEN by --selftest under 22c(b))")
        print(f"[{fam}] {vline(v)}")
        if v["outcome"] == "inconclusive":
            print(f"[{fam}] INCONCLUSIVE (22d): not one probe moved between the arms.")
        elif v["outcome"] == "no detected change":
            print(f"[{fam}] NO DETECTED CHANGE. The floor of all floors is "
                  f"{FLOOR_OF_ALL_FLOORS}; at {v['discordant']} discordant pairs the "
                  f"bar is a net of {v['net_needed']}. Do not lower it.")
        else:
            print(f"[{fam}] {v['outcome']}.")
    nq, o, n, *_ = verdicts["placebo"]
    print()
    if o == n:
        print(f"[placebo] CONTROL HOLDS: both arms score {o}/{nq}. Nothing but the "
              f"feature is moving.")
    else:
        print(f"[placebo] 🔴 CONTROL BROKEN: old {o}/{nq} vs new {n}/{nq}. Something "
              f"other than the feature differs between the arms; the fence and depth "
              f"numbers above are not attributable.")

    if a.json:
        dest = Path(a.json)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as fh:
            for arm in ("old", "new"):
                for row in out[arm].values():
                    fh.write(json.dumps(row, sort_keys=True) + "\n")
        print(f"\nper-probe rows ({sum(len(v) for v in out.values())}) -> {a.json}")
    return 0


def cmd_sweep(a) -> int:
    """Dose-response over the subject's prose `tf`: at what weight of ordinary
    body evidence does a mis-mined heading stop deciding the answer?

    🔴 **This exists because a single `tf` is the author's choice and says so.**
    `hit@1` flipping 0/30 -> 30/30 at one `tf` is partly a statement about that
    `tf`. The curve is not: it reports how much genuine prose evidence a correct
    document needs before a decoy's fenced comment — weighted `bm25f.heading`
    3.0 in the pre-W-115 arm — stops outranking it.

    It is also the diagnostic. A family that is Inconclusive at every `tf` has an
    endpoint that cannot move, which is decision 22d and not a null.
    """
    import contextlib
    import io
    rows = []
    print(f"{'subject tf':>10}  {'family':>8}  {'hit@1 old':>10}  {'hit@1 new':>10}  "
          f"{'decoy@1 o->n':>12}  {'p':>9}  outcome")
    for tf in a.tf_values:
        ns = argparse.Namespace(dest=a.corpus, filler=a.filler, tf=tf)
        with contextlib.redirect_stdout(io.StringIO()):
            cmd_gen(ns)
        corpus = Path(a.corpus)
        with contextlib.redirect_stdout(io.StringIO()):
            probes, out = _both_arms(corpus)
        for fam in ("fence", "depth", "placebo"):
            ids = [p["id"] for p in probes if p["family"] == fam]
            o = sum(1 for i in ids if out["old"][i]["hit1"])
            n = sum(1 for i in ids if out["new"][i]["hit1"])
            do = sum(1 for i in ids if out["old"][i]["decoy_at_1"])
            dn = sum(1 for i in ids if out["new"][i]["decoy_at_1"])
            # ⚠ **Secondary, and it is NOT the pre-registered endpoint.** The
            # bar is on `hit@1`. `decoy@1` was already in the instrument when it
            # was committed, and it is the more sensitive question — *does a
            # document whose only mention is an incidental shell comment take
            # the top slot* — so it is reported and labelled, never adjudicated.
            b = sum(1 for i in ids if out["new"][i]["hit1"] and not out["old"][i]["hit1"])
            c = sum(1 for i in ids if out["old"][i]["hit1"] and not out["new"][i]["hit1"])
            v = vrule(b, c, better="shipped better", worse="pre-W-115 better")
            print(f"{tf:>10}  {fam:>8}  {o:>5} /{len(ids):<4}  {n:>5} /{len(ids):<4}  "
                  f"{do:>6} -> {dn:<4}  {v['p']:>9.4f}  {v['outcome']}")
            rows.append({"subject_tf": tf, "family": fam, "n": len(ids),
                         "hit1_old": o, "hit1_new": n,
                         "decoy1_old": do, "decoy1_new": dn, **v})
        print()
    if a.json:
        dest = Path(a.json); dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                        encoding="utf-8")
        print(f"sweep rows ({len(rows)}) -> {a.json}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    g = sub.add_parser("gen"); g.add_argument("--dest", required=True)
    g.add_argument("--filler", type=int, default=120)
    g.add_argument("--tf", type=int, default=4,
                   help="how many times a SUBJECT names its topic in prose")
    g.set_defaults(fn=cmd_gen)
    s = sub.add_parser("selftest"); s.add_argument("--corpus", required=True)
    s.set_defaults(fn=cmd_selftest)
    r = sub.add_parser("run"); r.add_argument("--corpus", required=True)
    r.add_argument("--json"); r.set_defaults(fn=cmd_run)
    w = sub.add_parser("sweep"); w.add_argument("--corpus", required=True)
    w.add_argument("--tf-values", type=int, nargs="+", dest="tf_values",
                   default=[1, 2, 3, 4, 6, 8])
    w.add_argument("--filler", type=int, default=120)
    w.add_argument("--json"); w.set_defaults(fn=cmd_sweep)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
