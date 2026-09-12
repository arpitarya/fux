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
corpus cannot show you a change it never triggers — ADR-RS decision 23b, which
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

⚠ **`--selftest` is the headroom proof (ADR-RS decision 22c(b)).** It asserts
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

#: ADR-RS decision 19 — the floor of all floors. Never lowered to fit a result.
FLOOR = 6

SEED = 20260912

#: Nonsense topic tokens: `df` is controlled by the generator rather than by
#: whatever English happens to be common, so a probe's difficulty is a property
#: of the corpus and not of the language.
TOPICS = [
    "zolfrane", "quendrix", "marbeth", "vintaro", "kelspar", "oridune",
    "thalmet", "pyrrocol", "bexwald", "cindrol", "nyquath", "sperrin",
    "drovane", "ashkeld", "morrivan", "telquist", "havorne", "brendisk",
    "orsalis", "wickmare",
]

#: The subjects the decoys are genuinely about, so a decoy is a real document
#: rather than a sentence with a code block stapled to it.
DECOY_SUBJECTS = [
    "certificate rotation", "log shipping", "disk pressure", "queue drain",
    "index compaction", "replica failover", "token refresh", "cache warmup",
    "backup verification", "socket tuning", "batch replay", "mirror sync",
    "quota audit", "shard rebalance", "trace sampling", "alert routing",
    "image pruning", "session eviction", "route reload", "credential vaulting",
]

FILLER_TOPICS = [
    "dock scheduling", "reefer maintenance", "driver rostering", "fuel reconciliation",
    "pallet labelling", "customs paperwork", "yard marshalling", "tyre inspection",
]


# ---------------------------------------------------------------------------
# gen
# ---------------------------------------------------------------------------

def _subject_md(topic: str, i: int) -> str:
    """A document that IS about `topic`: title, headings and prose all say so."""
    return (
        f"---\ntitle: {topic.title()} handling procedure\n---\n\n"
        f"# {topic.title()} handling procedure\n\n"
        f"This procedure covers {topic} end to end. Every {topic} event is logged\n"
        f"against the {topic} register before the shift closes.\n\n"
        f"## When {topic} is detected\n\n"
        f"- Raise a {topic} ticket within fifteen minutes.\n"
        f"- Record the {topic} reading and the ambient reading together.\n"
        f"- A second {topic} reading is taken thirty minutes later.\n\n"
        f"## Escalation for {topic}\n\n"
        f"If two consecutive {topic} readings exceed the band, escalate to the duty\n"
        f"supervisor. The supervisor owns the {topic} decision from that point.\n\n"
        f"## Records\n\n"
        f"The {topic} register is retained for seven years. Reference {i:04d}.\n"
    )


def _decoy_md(topic: str, subject: str, i: int) -> str:
    """A document about `subject` whose ONLY link to `topic` is a fenced shell
    comment — incidental, not a section, and not what the document is about."""
    return (
        f"---\ntitle: {subject.title()} runbook\n---\n\n"
        f"# {subject.title()} runbook\n\n"
        f"This runbook covers {subject}. Run it from the operations host after the\n"
        f"nightly window closes.\n\n"
        f"## Procedure\n\n"
        f"```bash\n"
        f"# {topic.title()} check before we start\n"
        f"opsctl preflight --stage {subject.split()[0]}\n"
        f"\n"
        f"# {topic.title()} threshold, do not edit\n"
        f"opsctl set-threshold --value 4\n"
        f"\n"
        f"# {topic.title()} teardown\n"
        f"opsctl teardown --force\n"
        f"```\n\n"
        f"## Rollback\n\n"
        f"Re-run the preflight and stop. Reference {i:04d}.\n"
    )


def _subject_yaml(topic: str, i: int) -> str:
    """`topic` as a TOP-LEVEL key — a heading in both arms."""
    return (
        f"{topic}:\n"
        f"  owner: duty supervisor\n"
        f"  window: nightly\n"
        f"  note: the {topic} policy is reviewed each quarter\n"
        f"reference: R{i:04d}\n"
    )


def _decoy_yaml(topic: str, subject: str, i: int) -> str:
    """`topic` buried at depth 5 — a heading in the OLD arm, bold body in the new."""
    return (
        f"{subject.replace(' ', '_')}:\n"
        f"  stages:\n"
        f"    preflight:\n"
        f"      checks:\n"
        f"        {topic}: threshold four, do not edit\n"
        f"      note: the {subject} preflight runs first\n"
        f"  reference: R{i:04d}\n"
    )


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
    (dest / ".fux").mkdir(parents=True, exist_ok=True)
    (dest / ".fux" / "pii.toml").write_text("", encoding="utf-8")

    rng = random.Random(SEED)
    probes: list[dict] = []
    files: dict[str, str] = {}

    for i, (topic, subject) in enumerate(zip(TOPICS, DECOY_SUBJECTS)):
        # -- family `fence`: markdown, a shell comment that looks like a heading
        s = f"docs/{i:03d}-{topic}-procedure.md"
        d = f"docs/{i:03d}-{subject.replace(' ', '-')}-runbook.md"
        files[s] = _subject_md(topic, i)
        files[d] = _decoy_md(topic, subject, i)
        probes.append({"id": f"f{i:02d}", "family": "fence", "query": topic,
                       "relevant": s, "decoy": d,
                       "why": f"the runbook's only {topic} is a fenced shell comment"})

        # -- family `depth`: yaml, a fifth-level key
        sy = f"docs/{i:03d}-{topic}-policy.yaml"
        dy = f"docs/{i:03d}-{subject.replace(' ', '-')}-pipeline.yaml"
        files[sy] = _subject_yaml(topic, i)
        files[dy] = _decoy_yaml(topic, subject, i)
        probes.append({"id": f"d{i:02d}", "family": "depth", "query": f"{topic} policy",
                       "relevant": sy, "decoy": dy,
                       "why": f"the pipeline's only {topic} is a depth-5 key"})

        # -- family `placebo`: the same question shape with NO decoy mechanism.
        #    Both arms must score it identically; if they do not, something
        #    other than the feature is moving and the run is void.
        sp = f"docs/{i:03d}-{topic}-charter.md"
        files[sp] = (
            f"---\ntitle: {topic.title()} charter\n---\n\n"
            f"# {topic.title()} charter\n\n"
            f"The {topic} charter states who owns {topic} and who reviews it.\n"
            f"There is no code in this document. Reference C{i:04d}.\n")
        probes.append({"id": f"p{i:02d}", "family": "placebo", "query": f"{topic} charter",
                       "relevant": sp, "decoy": None,
                       "why": "no fence and no deep key — neither arm can differ"})

    for i in range(a.filler):
        rel, body = _filler(rng, i)
        files[f"docs/{rel}"] = body

    for rel, body in sorted(files.items()):
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    (dest / "probes.jsonl").write_text(
        "".join(json.dumps(p, sort_keys=True) + "\n" for p in probes), encoding="utf-8")
    (dest / "fux.toml").write_text(
        '[sources]\ndirs = ["docs"]\n'
        'types = [".md", ".txt", ".yaml", ".json", ".jsonl", ".csv"]\n',
        encoding="utf-8")
    print(f"{len(files)} documents, {len(probes)} probes -> {dest}")
    print(f"  fence   {sum(1 for p in probes if p['family'] == 'fence')}")
    print(f"  depth   {sum(1 for p in probes if p['family'] == 'depth')}")
    print(f"  placebo {sum(1 for p in probes if p['family'] == 'placebo')}")
    return 0


# ---------------------------------------------------------------------------
# the two arms
# ---------------------------------------------------------------------------

#: Run inside a fresh interpreter so the `old` arm's patches cannot leak into
#: the `new` arm through a warm module cache.
ARM_DRIVER = r'''
import json, re, sys
from pathlib import Path

arm, root, probes_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

if arm == "old":
    import fux.ingest.extract as E
    import fux.decode.json as J

    # The pre-W-115 grammar, verbatim from 94231b2: one regex, no fence
    # awareness, applied to every extension without its own pattern.
    _OLD = re.compile(r"^(#{1,6})\s+(?P<text>.+?)\s*$", re.MULTILINE)

    def _old_headings_and_body(rel_path, body):
        grammar = E._grammar(rel_path)
        if grammar is None:
            grammar = _OLD
        return ([m.group("text").strip() for m in grammar.finditer(body)],
                grammar.sub("", body))

    E._headings_and_body = _old_headings_and_body

    # The pre-W-115 label: a container key is a heading at EVERY depth.
    J._label = lambda label, depth: "#" * min(depth, 6) + " " + label

import fux.decode.jsonl as JL, fux.decode.yaml as YA, fux.decode.xml as XM
for mod in (JL, YA, XM):
    if hasattr(mod, "_label"):
        mod._label = J._label if arm == "old" else mod._label

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
    """ADR-RS 22c(b): the arms must disagree about the decoys and about nothing
    else. Asserted on extraction, before any ranking number exists."""
    corpus = Path(a.corpus)
    probes = [json.loads(l) for l in (corpus / "probes.jsonl").read_text().splitlines() if l.strip()]
    script = r'''
import json, re, sys
from pathlib import Path
sys.path.insert(0, "")
import fux.ingest.extract as E
import fux.decode.json as J
from fux.ingest.parse import parse_document
from fux.decode import decode

_OLD = re.compile(r"^(#{1,6})\s+(?P<text>.+?)\s*$", re.MULTILINE)
def old_h(rel, body):
    g = E._grammar(rel) or _OLD
    return [m.group("text").strip() for m in g.finditer(body)], g.sub("", body)

corpus = Path(sys.argv[1])
out = {}
for rel in sorted(json.loads(sys.argv[2])):
    p = corpus / rel
    raw = p.read_bytes()
    try:
        text = decode(p.name, raw)
    except Exception:
        text = raw.decode("utf-8", "replace")
    doc = parse_document(text)
    new = E._headings_and_body(rel, doc.body)[0]
    old = old_h(rel, doc.body)[0]
    out[rel] = {"new": new, "old": old, "differs": new != old}
print(json.dumps(out))
'''
    rels = sorted({p["relevant"] for p in probes} | {p["decoy"] for p in probes if p["decoy"]})
    drv = corpus / "_selftest.py"
    drv.write_text(script, encoding="utf-8")
    r = subprocess.run([str(PY), str(drv), str(corpus), json.dumps(rels)],
                       cwd=str(corpus), text=True, capture_output=True, check=False)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return 1
    got = json.loads(r.stdout)
    decoys = {p["decoy"] for p in probes if p["decoy"]}
    relevant = {p["relevant"] for p in probes}
    d_differ = sum(1 for rel in decoys if got[rel]["differs"])
    r_differ = sum(1 for rel in relevant if got[rel]["differs"])
    print(f"decoys whose heading set differs between the arms:   {d_differ} / {len(decoys)}")
    print(f"subjects whose heading set differs between the arms: {r_differ} / {len(relevant)}")
    ok = d_differ == len(decoys) and r_differ == 0
    print()
    if ok:
        print("SELFTEST PASSES (ADR-RS 22c(b)): every decoy is separable by the "
              "property under test and no subject is. Headroom is PROVEN, not observed.")
    else:
        print("SELFTEST FAILS: the arms do not isolate the property under test. "
              "Any number from this corpus measures something else.")
    return 0 if ok else 1


def cmd_run(a) -> int:
    corpus = Path(a.corpus)
    probes_path = corpus / "probes.jsonl"
    probes = [json.loads(l) for l in probes_path.read_text().splitlines() if l.strip()]
    scratch = corpus.parent
    out = {}
    for arm in ("old", "new"):
        dest = scratch / f"rows-{arm}.jsonl"
        _run_arm(arm, corpus, probes_path, dest)
        out[arm] = {json.loads(l)["id"]: json.loads(l)
                    for l in dest.read_text().splitlines() if l.strip()}

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
        disc, net = b + c, abs(b - c)
        head_imp = sum(1 for p in probes if p["family"] == fam
                       and not (out["old"][p["id"]]["hit1"] and out["new"][p["id"]]["hit1"]))
        head_reg = sum(1 for p in probes if p["family"] == fam
                       and (out["old"][p["id"]]["hit1"] or out["new"][p["id"]]["hit1"]))
        print(f"[{fam}] headroom improvement {head_imp}/{nq} · regression {head_reg}/{nq} "
              f"(ADR-RS 22b, PROVEN by --selftest under 22c(b))")
        if disc == 0:
            print(f"[{fam}] INCONCLUSIVE (22d): not one probe moved between the arms.")
        elif net >= FLOOR:
            better = "NEW (shipped W-115)" if b > c else "OLD (pre-W-115)"
            print(f"[{fam}] {better} RANKS BETTER: discordant {disc}, net {net}, "
                  f"floor {FLOOR}. b={b} probes the shipped arm gets right and the "
                  f"old arm does not; c={c} the other way.")
        else:
            print(f"[{fam}] NO DETECTED CHANGE: discordant {disc}, net {net}, below "
                  f"the floor of {FLOOR}. Do not lower the floor.")
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="verb", required=True)
    g = sub.add_parser("gen"); g.add_argument("--dest", required=True)
    g.add_argument("--filler", type=int, default=120); g.set_defaults(fn=cmd_gen)
    s = sub.add_parser("selftest"); s.add_argument("--corpus", required=True)
    s.set_defaults(fn=cmd_selftest)
    r = sub.add_parser("run"); r.add_argument("--corpus", required=True)
    r.add_argument("--json"); r.set_defaults(fn=cmd_run)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
