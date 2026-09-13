#!/usr/bin/env python3
"""The third arm of the differential law: Python's reader against Node's.

W-107 Phase 1b. **The harness exists before the code it checks** — this is a
~5 000-line transcription where a wrong last bit is invisible until something
fires, so the thing that catches lies is written first and passes trivially
(Python vs Python) before any `node/` file exists.

Compares per [PRE-REG-NODE-2](../../work/benchmark/PRE-REGISTRATION-NODE-2.md)
§3's field table, on **PARSED values, never on stdout bytes** — W-107 hazard
H2: Python prints `--json` with `ensure_ascii=True` and `JSON.stringify` does
not, so a byte diff fails on the first em-dash and measures nothing about the
engine.

  `id`, `loc`, order, `title`, `archived`, `tie`   byte-equal
  `score`                                          equal after round(9)

Usage — the corpus is an argument, and a rung is resolved and verified:

    node_arm.py .                          this repo's own index (the CI arm)
    node_arm.py --rung rung-00100          a golden-ladder rung, in fux-lab
    node_arm.py --rung rung-10000 --evidence work/regression/<run>/evidence/

⚠ **The corpus root and the engine root are two different things**, and
conflating them is why this file used to be unable to run on a rung at all:
`sys.path` must point at *this* checkout's `src/`, while the index being read
lives wherever the corpus is. A rung has no `src/`.

🔴 **The Python side goes through `run_query`, the same seam `fux find` uses.**
Calling `scan.ask` directly — which is what this file did until 2026-09-12 —
skips `.fux/tune.toml`, the archived weighting and the reranker. **The arm was
green because both sides ignored the same things**, which is the failure
`queryset.py`'s docstring names: a harness authored after the thing it checks
gets authored to pass.

🔴 **Two arms, because a discordance has to be attributable** (`CLAUDE.md`
§"Hard-won build knowledge" — keep a diagnostic arm that borrows, it is how a
loss gets attributed):

| `--python-tune on` (default) | **the contract** — what `fux find` answers on this corpus, tune and all. A discordance means the two readers disagree, whatever the cause |
| `--python-tune off` | **the transcription** — `--no-tune` on the Python side (SR-TUNE decision 11), which is the engine's own answer. A discordance here is a Node transcription defect and nothing else |

They are the same run on a corpus whose tune is all-defaults, which is every
golden rung today. They differ on **this repo**, whose `.fux/tune.toml` sets
`rerank_weight = 0.3`. The banner prints the delta so an evidence file never
has to be guessed at.

⚠ **`--no-tune` is passed to BOTH readers or to neither** (2026-09-12). Until
Node read the tune file there was nothing to flip on its side; now there is,
and flipping only Python's would compare a tuned reader against an untuned one
and report `.fux/tune.toml` as a transcription defect.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

#: This checkout — the engine under test and the Node entry point. Never the
#: corpus: a golden rung is a bare repo of documents with no `src/`.
ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

#: 🔴 **The sixth surface, and it is the one a CONSUMER runs.** Every other
#: surface here reads `node/fux.mjs` and its module tree; what `fux setup`
#: vendors and npm publishes is the BUNDLE (SR-NODE-SEARCH decisions 13-14,
#: L10). Shipping one artefact and measuring another is decisions 9-12 in a new
#: costume — *a transcription is only as true as the surface the instrument is
#: aimed at* — so the arm builds the bundle and compares it against the tree it
#: was built from, on whole parsed payloads.
_BUNDLE: "Path | None" = None

sys.path.insert(0, str(ENGINE / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rungs  # noqa: E402
from fux.query import run_query  # noqa: E402
from fux.query.headings import headings_for  # noqa: E402
from fux.store import reader as py_reader  # noqa: E402

#: Fields compared byte-equal. `score` is handled separately — SR-RANKING 8a.
EXACT = ("id", "loc", "title", "archived", "tie")

#: Every confidence field compared byte-equal. `coverage`, `separation` and
#: `doc_coverage` are already rounded to 4 places by `signals`, so they are
#: exact comparisons and not tolerances.
CONF_FIELDS = (
    "band", "answerable", "coverage", "separation", "separation_floor",
    "doc_coverage", "doc_coverage_floor", "support", "verified", "missing",
)

#: Queries that pin a hazard rather than exercise the corpus. They run on every
#: corpus, whatever else the set holds, because the thing they catch is a
#: property of the two runtimes and not of the documents.
#:
#:   `zzqq`      H1 — the adversarial corpus's tied ids straddling U+FFFF
#:   `nonascii`  H2 — a title and headings outside ASCII
#:   ``/`   `    the empty and whitespace-only paths through the analyzer
PINS = ("zzqq", "nonascii", "", "   ", "zzzzzznomatch")

#: The default set when the corpus is this repo: hand-written, and left exactly
#: as it was so the CI arm's meaning does not change under this rewrite.
REPO_QUERIES = (
    "rollback", "ranking", "index format", "confidence band", "the",
    "decoder", "pii redaction", "graph plane", "accelerator", "refer",
    "getUserName", "BM25F", "sha256", "fux-engine", "archived results",
    "how do we roll back a release", "L1 zero cost", "tune.toml",
    "chunking", "regression evidence", "supersedes", "node read plane",
    "docs/adr", "answer verdict freshness",
)


def bundle_entry() -> Path:
    """Build the published bundle once per run and return its path.

    Built rather than found: a bundle on disk could be from another checkout,
    and the question this surface answers is whether the artefact THIS tree
    publishes answers what THIS tree's modules answer.
    """
    global _BUNDLE
    if _BUNDLE is None:
        import tempfile

        from fux.store import nodebundle

        out = Path(tempfile.mkdtemp(prefix="fux-arm-bundle-"))
        nodebundle.write(ENGINE / "node", out)
        _BUNDLE = out / nodebundle.ENTRY
    return _BUNDLE


class Arm:
    """One corpus, both readers, and the record map they are compared over."""

    def __init__(self, root: Path, *, use_tune: bool = True) -> None:
        self.root = root
        self.use_tune = use_tune
        # Built once. The previous shape re-scanned every shard for every
        # result row of every query, which is O(corpus x results) and is what
        # made a 10 000-document rung impossible rather than merely slow.
        self.records: dict[str, dict] = py_reader.read_index(root)

    # -- the two readers ------------------------------------------------------

    def node(self, verb: str, query: str, top: int, extra: tuple[str, ...] = (),
             entry: "Path | None" = None) -> dict:
        # 🔴 `--no-tune` goes to BOTH sides or to neither. Since 2026-09-12 Node
        # reads `.fux/tune.toml` too (SR-NODE-SEARCH decision 8, closed), so a
        # transcription arm that flipped only the Python side would compare a
        # tuned reader against an untuned one and report the tune file as a
        # transcription defect — the same both-sides-blind failure in reverse.
        # `top=None` is the graph lane: `explain`/`graph`/`path` have no --top,
        # and they carry their own `--no-tune` from `compare_verb` (`explain`
        # takes none at all), so the automatic flag applies to the ranking
        # verbs only.
        depth = ("--top", str(top)) if top is not None else ()
        no_tune = () if (self.use_tune or top is None) else ("--no-tune",)
        proc = subprocess.run(
            ["node", str(entry or NODE_ENTRY), verb, query, "--json", *depth, *no_tune, *extra],
            capture_output=True, text=True, encoding="utf-8", cwd=self.root,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"node exited {proc.returncode}: {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    def python(self, query: str, top: int, *, want_confidence: bool) -> dict:
        """What `fux find`/`fux ask` computes, through the CLI's own seam."""
        out: dict = {} if want_confidence else None
        results, _path = run_query(
            self.root, query, top, confidence_out=out, use_tune=self.use_tune
        )
        rows = [
            {"id": r.id, "loc": r.loc, "title": r.title, "score": r.score,
             "archived": r.archived, "tie": r.tie}
            for r in results
        ]
        if not want_confidence:
            return {"results": rows}
        for row, r in zip(rows, results):
            row["headings"] = headings_for(self.records.get(r.id), query)
        confidence = out.get("confidence")
        return {"results": rows, "confidence": confidence.as_dict() if confidence else None}

    # -- the comparisons ------------------------------------------------------

    def compare_find(self, query: str, top: int) -> list[str]:
        py = self.python(query, top, want_confidence=False)["results"]
        nd = self.node("find", query, top)["results"]
        out: list[str] = []
        if len(py) != len(nd):
            return [f"find {query!r}: {len(py)} python results vs {len(nd)} node"]
        for i, (p, n) in enumerate(zip(py, nd)):
            out.extend(self._fields(f"find {query!r} [{i}]", p, n, EXACT))
        return out

    def compare_ask(self, query: str, top: int) -> list[str]:
        py = self.python(query, top, want_confidence=True)
        nd = self.node("ask", query, top, ("--band",))
        out: list[str] = []
        if len(py["results"]) != len(nd["results"]):
            return [f"ask {query!r}: {len(py['results'])} python vs {len(nd['results'])} node"]
        for i, (p, n) in enumerate(zip(py["results"], nd["results"])):
            out.extend(self._fields(f"ask {query!r} [{i}]", p, n, (*EXACT, "headings")))
        pc, nc = py["confidence"], nd.get("confidence")
        if nc is None:
            out.append(f"ask {query!r}: node emitted no confidence block under --band")
        elif pc is None:
            out.append(f"ask {query!r}: python emitted no confidence block")
        else:
            for f in CONF_FIELDS:
                if pc[f] != nc[f]:
                    out.append(f"ask {query!r} confidence.{f}: python={pc[f]!r} node={nc[f]!r}")
        return out

    # -- the graph lane -------------------------------------------------------
    #
    # 🔴 **These compare the two CLIs, not two library calls**, and that is the
    # lesson of the tune find restated: a harness that calls the pure functions
    # on both sides tests the functions and not the verbs, and the divergence
    # that bit W-107 lived in the VERB. Python goes through a subprocess here
    # for one concrete reason beyond symmetry — `graph._root()` reads the
    # process's cwd, and this harness runs its comparisons on a thread pool, so
    # an in-process call would have to `chdir` a shared process.

    def python_cli(self, verb: str, argv: tuple[str, ...]) -> dict:
        env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
        proc = subprocess.run(
            [sys.executable, "-m", "fux", verb, *argv, "--json"],
            capture_output=True, text=True, encoding="utf-8", cwd=self.root, env=env,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"python exited {proc.returncode}: {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    def compare_verb(self, verb: str, argv: tuple[str, ...], *, tunable: bool = True) -> list[str]:
        """One non-ranking verb, both CLIs, compared as WHOLE parsed payloads.

        Whole-payload rather than a field list, deliberately: `explain`, `graph`
        and `path` carry no score to tolerance, so every byte of meaning is in
        the structure — and comparing a field list is exactly what would let the
        two emit different KEY NAMES without the arm noticing.

        `tunable=False` is `explain`, which takes no `--no-tune` on either side
        because it reads no tunable.
        """
        flags = ("--no-tune",) if (tunable and not self.use_tune) else ()
        py = self.python_cli(verb, argv + flags)
        nd = self.node(verb, argv[0], None, tuple(argv[1:]) + flags)
        if py == nd:
            return []
        return [f"{verb} {' '.join(argv)!r}: python={json.dumps(py, sort_keys=True)[:400]} "
                f"node={json.dumps(nd, sort_keys=True)[:400]}"]

    # -- the MCP surface ------------------------------------------------------
    #
    # 🔴 **Added 2026-09-12, and it found a shipped defect on the first run.**
    # Node's three tool handlers read `args.id` where `mcp-tools.json`
    # advertises `path`, so `fux_passage` and `fux_related` returned an empty
    # answer to every conformant client — from a server reporting success, in a
    # package already on npm. Nothing could have caught it except comparing the
    # two servers, because each was internally consistent.

    #: `ranked_by` names WHICH candidate path answered, and the two runtimes
    #: legitimately differ: Python's MCP surface opts into the accelerator and
    #: Node has none (SR-NODE-SEARCH decision 10). The differential law says
    #: the two paths return the same documents, so the label is the only honest
    #: difference — excluded by name, never by a loosened comparison.
    MCP_EXCLUDE = ("ranked_by",)

    def mcp(self, runner: list[str], calls: list[dict]) -> list[dict]:
        lines = "\n".join(json.dumps(c) for c in calls) + "\n"
        env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
        proc = subprocess.run(runner, input=lines, capture_output=True, text=True, encoding="utf-8",
                              cwd=self.root, env=env)
        if proc.returncode != 0:
            raise RuntimeError(f"{runner[0]} exited {proc.returncode}: {proc.stderr.strip()}")
        return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]

    def compare_mcp(self, calls: list[dict]) -> list[str]:
        """Both MCP servers, one stdio session each, compared call by call."""
        py = self.mcp([sys.executable, "-m", "fux", "mcp"], calls)
        nd = self.mcp(["node", str(NODE_ENTRY), "mcp"], calls)
        out: list[str] = []
        if len(py) != len(nd):
            return [f"mcp: {len(py)} python responses vs {len(nd)} node"]
        for call, a, b in zip(calls, py, nd):
            name = (call.get("params") or {}).get("name", call.get("method"))
            pa = (a.get("result") or {}).get("structuredContent", a)
            nb = (b.get("result") or {}).get("structuredContent", b)
            if isinstance(pa, dict) and isinstance(nb, dict):
                pa = {k: v for k, v in pa.items() if k not in self.MCP_EXCLUDE}
                nb = {k: v for k, v in nb.items() if k not in self.MCP_EXCLUDE}
            if pa != nb:
                out.append(f"mcp {name}: python={json.dumps(pa, sort_keys=True)[:300]} "
                           f"node={json.dumps(nb, sort_keys=True)[:300]}")
        return out

    # -- the LIBRARY surface --------------------------------------------------
    #
    # 🔴 **R3's third surface, and it was diverging too.** W-107 R3 is *"one
    # API, three surfaces"* — CLI JSON, Python objects, Node objects. The arm
    # checked one of the three. Measured 2026-09-12: `fux.api.find` called
    # `scan_ask` directly, so `from fux import open` returned a different
    # RANKING from `fux find` on this repo (`graph plane`: 6.392573 against
    # 8.310345) — the same defect as SR-NODE-SEARCH decision 8, in Python.
    # Node's half additionally dropped the `ordinal` key from every passage.

    #: The six methods, called identically on both sides. Kept as source rather
    #: than a data structure because the two runtimes have to SPELL the call,
    #: and the spelling is half of what "the same API" means.
    API_JS = """
import { open } from %(entry)s;
const ix = await open(%(root)s);
process.stdout.write(JSON.stringify({
  find: await ix.find(%(q)s, { top: 3 }),
  ask: (await ix.ask(%(q)s, { top: 3 })).asDict(),
  explain: await ix.explain(%(doc)s),
  graph: await ix.graph(%(q)s, { hops: 1, top: 3 }),
  path: await ix.path(%(doc)s, %(doc2)s, { hops: 3 }),
  answer: (await ix.answer(%(q)s)).asDict(),
}));
"""

    API_PY = """
import json, fux
ix = fux.open(%(root)s)
print(json.dumps({
  "find": [r.as_dict() for r in ix.find(%(q)s, top=3)],
  "ask": ix.ask(%(q)s, top=3).as_dict(),
  "explain": ix.explain(%(doc)s),
  "graph": ix.graph(%(q)s, hops=1, top=3),
  "path": ix.path(%(doc)s, %(doc2)s, hops=3),
  "answer": ix.answer(%(q)s).as_dict(),
}))
"""

    def compare_api(self, query: str, doc: str, doc2: str) -> list[str]:
        subs = {
            # `.as_uri()`, not `str()`: an ESM specifier is a URL, and Node on
            # Windows rejects `C:\...` with ERR_UNSUPPORTED_ESM_URL_SCHEME.
            "entry": json.dumps((ENGINE / "node" / "src" / "index.mjs").as_uri()),
            "root": json.dumps(str(self.root)),
            "q": json.dumps(query), "doc": json.dumps(doc), "doc2": json.dumps(doc2),
        }
        env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
        runs = {
            "node": (["node", "--input-type=module", "-e", self.API_JS % subs], None),
            "python": ([sys.executable, "-c", self.API_PY % subs], env),
        }
        got = {}
        for name, (argv, e) in runs.items():
            proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", cwd=self.root, env=e)
            if proc.returncode != 0:
                return [f"api ({name}) exited {proc.returncode}: {proc.stderr.strip()[:300]}"]
            # Python's `answer` prints a stderr note; stdout is the payload, and
            # the LAST line of it is the JSON (a verb may declare above it).
            got[name] = json.loads(proc.stdout.strip().splitlines()[-1])
        out = []
        for method in sorted(set(got["python"]) | set(got["node"])):
            py_v, nd_v = got["python"].get(method), got["node"].get(method)
            if method == "answer":
                # 🔴 **The one asymmetry, and what is asserted instead of
                # equality.** Python decodes a cited document before chunking
                # it; Node has no decoders and skips such a document rather than
                # citing line numbers into text the index never held
                # (SR-NODE-SEARCH decision 11).
                #
                # **The invariant is checked on EVERY answer**: nothing Node
                # cites may be a decoded document. That is the contract, it is
                # exact, and it does not depend on what Python did.
                decoded = self._decoded_citations(nd_v)
                if decoded:
                    out.append(f"api answer: node cited a DECODED document it cannot "
                               f"reproduce: {sorted(decoded)}")
                # **Equality is asserted only when the CANDIDATE SETS can
                # match.** Once Python refers a decoded document that Node
                # skipped, the two rescore over different passage populations —
                # `df` is computed across the candidate set — so every score
                # downstream legitimately differs. Comparing there would not be
                # a weaker check, it would be a meaningless one.
                if self._decoded_citations(py_v):
                    continue
            if py_v != nd_v:
                out.append(f"api {method}: python={json.dumps(py_v, sort_keys=True)[:300]} "
                           f"node={json.dumps(nd_v, sort_keys=True)[:300]}")
        return out

    # -- the BUNDLE surface ---------------------------------------------------
    #
    # 🔴 **What a consumer actually executes.** `.fux/node/fux.mjs` and the npm
    # tarball's entry point are one generated file; `node/src/**` never leaves
    # this repository (L10). The bundler is deterministic, which makes the
    # bytes reproducible — it does NOT make them right, and "the concatenation
    # compiled" is not the same claim as "it answers the same".

    #: Verbs compared through both Node entry points, as whole payloads. Whole
    #: rather than field-wise for `compare_verb`'s reason: a renamed key is
    #: exactly the kind of thing a bundling mistake could produce.
    BUNDLE_VERBS = ("find", "ask", "answer")

    def compare_bundle(self, verb: str, query: str, top: "int | None") -> list[str]:
        """One verb, the module tree against the bundle built from it."""
        extra = ("--band",) if verb == "ask" else ()
        tree = self.node(verb, query, top, extra)
        built = self.node(verb, query, top, extra, entry=bundle_entry())
        if tree == built:
            return []
        return [f"bundle {verb} {query!r}: tree={json.dumps(tree, sort_keys=True)[:300]} "
                f"bundle={json.dumps(built, sort_keys=True)[:300]}"]

    def compare_bundle_api(self, query: str, doc: str, doc2: str) -> list[str]:
        """The LIBRARY surface through the bundle — `exports` names it now.

        `node/package.json`'s `exports` left `./src/index.mjs` for the bundle
        with W-149, so `import { open } from "fux-engine"` resolves to this
        file for every npm consumer. An arm that only imported the module tree
        would be testing a path nobody's `node_modules` contains.
        """
        out = []
        for entry in (ENGINE / "node" / "src" / "index.mjs", bundle_entry()):
            subs = {
                "entry": json.dumps(entry.as_uri()), "root": json.dumps(str(self.root)),
                "q": json.dumps(query), "doc": json.dumps(doc), "doc2": json.dumps(doc2),
            }
            proc = subprocess.run(
                ["node", "--input-type=module", "-e", self.API_JS % subs],
                capture_output=True, text=True, encoding="utf-8", cwd=self.root,
            )
            if proc.returncode != 0:
                return [f"bundle api ({entry.name}) exited {proc.returncode}: "
                        f"{proc.stderr.strip()[:300]}"]
            out.append(json.loads(proc.stdout.strip().splitlines()[-1]))
        if out[0] == out[1]:
            return []
        return [f"bundle api: tree and bundle disagree on "
                f"{sorted(k for k in out[0] if out[0][k] != out[1].get(k))}"]

    def compare_bundle_mcp(self, calls: list[dict]) -> list[str]:
        """Both Node MCP servers — module tree and bundle — over one session each.

        The bundle resolves `mcp-tools.json` from a different directory shape
        than the tree does, and a wrong answer there is an `ENOENT` at the
        first `tools/list` on a consumer's machine and nowhere else.
        """
        tree = self.mcp(["node", str(NODE_ENTRY), "mcp"], calls)
        built = self.mcp(["node", str(bundle_entry()), "mcp"], calls)
        if tree == built:
            return []
        return [f"bundle mcp: {len(tree)} tree responses vs {len(built)} bundle, first "
                f"difference at {next((i for i, (a, b) in enumerate(zip(tree, built)) if a != b), None)}"]

    def _decoded_citations(self, payload: dict) -> set[str]:
        """The cited documents in `payload` that a DECODER produced.

        Asked of PYTHON's own decoder registry, never of a list transcribed
        here: the question is whether the two runtimes can see the same text,
        and only one of them is the authority on that.
        """
        from fux.decode import registry

        claimed = set(registry(self.root))
        body = (payload or {}).get("answer") or {}
        out = set()
        for passage in body.get("passages", []):
            stem = passage.get("loc", "").split(":L")[0].split("#p")[0]
            dot = stem.rfind(".")
            if dot >= 0 and stem[dot:].lower() in claimed:
                out.add(stem)
        return out

    @staticmethod
    def _fields(where: str, p: dict, n: dict, fields: tuple[str, ...]) -> list[str]:
        out = []
        for f in fields:
            if p[f] != n[f]:
                out.append(f"{where} {f}: python={p[f]!r} node={n[f]!r}")
        # SR-RANKING decision 8a — the sort key's own resolution, and the
        # tolerance Arpit ruled in Phase 0 (option b). NOT an invented epsilon.
        if round(p["score"], 9) != round(n["score"], 9):
            out.append(
                f"{where} score at round(9): "
                f"python={round(p['score'], 9)!r} node={round(n['score'], 9)!r} "
                f"(raw python={p['score']!r} node={n['score']!r})"
            )
        return out


def corpus_queries(root: Path, cap: int) -> list[str]:
    """A deterministic set drawn from the corpus's own vocabulary.

    `queryset.generate` builds from the *source documents* by a fixed rule, so
    a set cannot be curated toward a green result. It is capped by position in
    that fixed order — never sampled — because the full set is ~800 queries and
    each one costs a Node process.

    🔴 **Not the golden questions.** The arm compares two readers against each
    other and must never acquire a reason to open an answer key
    (PRE-REG-NODE-2 §4).
    """
    import queryset

    full = queryset.generate(root)
    step = max(1, len(full) // cap) if cap else 1
    return full[::step][:cap] if cap else full


def graph_lane_ready(root: Path) -> bool:
    """Can the graph verbs be compared on this corpus at all?

    🔴 **They are ASYMMETRIC and only one side is gated.** Python's
    `graph.plane.load` reads the derived `.fux/runtime/graph.json` and REFUSES
    when it is absent or stale; Node rebuilds the plane in memory from the
    committed records and answers either way (SR-NODE-SEARCH decision 9).

    So a corpus with no fresh build is one where the two readers *legitimately*
    differ, and running the comparison there would file Python's refusal as a
    discordance. **Skipped and said out loud**, never skipped quietly: a lane
    that silently does not run is how `find` went a month without its tune file.
    """
    from fux.derive import accel, format as derive_fmt

    try:
        return (derive_fmt.runtime_dir(root) / "graph.json").exists() and accel.is_fresh(root)
    except Exception:
        return False


def tune_delta(root: Path) -> str:
    """How this corpus's effective tune differs from the engine's defaults.

    Printed as a **run condition**, not a check. Both readers now honour every
    key listed here (W-107 R5's tune row, built 2026-09-12), so a delta is no
    longer a licence to expect disagreement — it says which weights produced
    the ranking an evidence file records, which is what makes the file
    re-readable a year later.
    """
    import dataclasses

    from fux.tune import Tune, load as load_tune

    live, defaults = load_tune(root), Tune()
    delta = {
        f.name: (getattr(defaults, f.name), getattr(live, f.name))
        for f in dataclasses.fields(live)
        if getattr(defaults, f.name) != getattr(live, f.name)
    }
    if not delta:
        return "all defaults — the contract and transcription arms are the same run"
    return ", ".join(f"{k}: default {d!r} -> {v!r}" for k, (d, v) in sorted(delta.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("corpus", nargs="?", default=None,
                    help="the repo whose index both readers read (default: .)")
    ap.add_argument("--rung", help=f"a golden-ladder rung: {', '.join(rungs.rung_names())}")
    ap.add_argument("--queries", choices=("fixed", "corpus"), default=None,
                    help="fixed = the hand-written repo set; corpus = derived from the "
                         "corpus vocabulary (the default for a rung)")
    ap.add_argument("--query-cap", type=int, default=120,
                    help="how many corpus-derived queries to run (0 = all)")
    ap.add_argument("--tops", default="1,5,20", help="result depths to compare")
    ap.add_argument("--jobs", type=int, default=8,
                    help="parallel comparisons; each costs one Node process")
    ap.add_argument("--evidence", type=Path, default=None,
                    help="directory for the per-query rows PRE-REG-NODE-2 §6 requires")
    ap.add_argument("--bundle-cap", type=int, default=8,
                    help="how many queries to run through the PUBLISHED BUNDLE as well as "
                         "the module tree (0 = skip). The bundle is what `fux setup` "
                         "vendors and npm ships, so it is the surface a consumer runs")
    ap.add_argument("--graph-cap", type=int, default=8,
                    help="how many explain/graph/path comparisons to run (0 = none). "
                         "Both sides rebuild the plane per call, so this is capped "
                         "rather than swept")
    ap.add_argument("--python-tune", choices=("on", "off"), default="on",
                    help="on = the contract arm (`.fux/tune.toml` applied, the default); "
                         "off = the transcription arm (`--no-tune`, the engine's own answer)")
    ap.add_argument("--skip-document-verify", action="store_true",
                    help="skip the per-document hash pass when resolving a rung")
    args = ap.parse_args()

    if args.rung and args.corpus:
        ap.error("--rung and a corpus path are two ways to say the same thing; pass one")

    label = args.rung or "corpus"
    if args.rung:
        try:
            root = rungs.resolve(args.rung, verify_documents=not args.skip_document_verify)
        except rungs.RungError as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
        print(f"rung     : {args.rung} at {root}")
        print(f"manifest : verified against work/golden/ladder/{args.rung}.{{index,sha256}}")
    else:
        root = Path(args.corpus or ".").resolve()
        print(f"corpus   : {root}")

    source = args.queries or ("corpus" if args.rung else "fixed")
    base = list(REPO_QUERIES) if source == "fixed" else corpus_queries(root, args.query_cap)
    queries = [*base, *(p for p in PINS if p not in base)]
    tops = [int(t) for t in args.tops.split(",")]

    use_tune = args.python_tune == "on"
    print(f"arm      : {'contract (tune applied)' if use_tune else 'transcription (--no-tune)'}")
    print(f"tune     : {tune_delta(root)}")

    arm = Arm(root, use_tune=use_tune)
    print(f"queries  : {len(queries)} ({source}) x tops {tops} x 2 verbs "
          f"= {len(queries) * len(tops) * 2} ranking comparisons")

    jobs = [(verb, q, top) for q in queries for top in tops
            for verb in ("find", "ask")]

    # 🔴 The graph lane, added 2026-09-12. The arm compared `find` and `ask`
    # only, so `explain`, `graph` and `path` were transcribed and never checked
    # — and they had diverged: different KEY NAMES in every one of the three
    # payloads, and Node's `graph` running its own breadth-first walk instead of
    # the PPR expansion. None of that is a thing the ranking arm could see.
    #
    # Ids are drawn by POSITION in sorted order, never sampled, so the set is a
    # property of the corpus and not of a run.
    if args.graph_cap and not graph_lane_ready(root):
        print("graph    : SKIPPED - no fresh derived plane on this corpus. Python's "
              "`explain`/`graph`/`path` refuse without `fux build`; Node's rebuild in "
              "memory and answer (SR-NODE-SEARCH decision 9). Run `fux build` to "
              "compare them.")
    elif args.graph_cap:
        ids = sorted(arm.records)
        step = max(1, len(ids) // args.graph_cap)
        picked = ids[::step][: args.graph_cap]
        jobs += [("explain", (doc,), None) for doc in picked]
        jobs += [("graph", (q,), None) for q in queries[: args.graph_cap] if q.strip()]
        jobs += [("path", (a, b), None) for a, b in zip(picked, picked[1:])]

    # 🔴 The sixth surface, added 2026-09-12 with W-149. The arm read the module
    # tree; consumers run the bundle. Cheap, because CI builds it anyway — and
    # the reason it is not merely a byte comparison is that a bundler can emit
    # something that parses, runs, and answers differently.
    if args.bundle_cap:
        picked_q = [q for q in queries if q.strip()][: args.bundle_cap]
        jobs += [("bundle", (verb, q), top)
                 for q in picked_q for top in tops[:1] for verb in arm.BUNDLE_VERBS]
        print(f"bundle   : {len(picked_q)} queries x {len(arm.BUNDLE_VERBS)} verbs "
              f"through the published artefact as well as the tree")

    if args.graph_cap:
        ids = sorted(arm.records)
        step = max(1, len(ids) // args.graph_cap)
        picked = ids[::step][: args.graph_cap]
        calls = [{"jsonrpc": "2.0", "id": 0, "method": "tools/list"}]
        for i, q in enumerate(queries[: args.graph_cap]):
            calls.append({"jsonrpc": "2.0", "id": len(calls), "method": "tools/call",
                          "params": {"name": "fux_search", "arguments": {"query": q, "k": 5}}})
        for doc in picked:
            loc = doc.split(":", 1)[1] if ":" in doc else doc
            calls.append({"jsonrpc": "2.0", "id": len(calls), "method": "tools/call",
                          "params": {"name": "fux_related", "arguments": {"path": loc}}})
            calls.append({"jsonrpc": "2.0", "id": len(calls), "method": "tools/call",
                          "params": {"name": "fux_passage",
                                     "arguments": {"path": loc, "line_start": 1, "line_end": 20}}})
        jobs.append(("mcp", tuple(json.dumps(c) for c in calls), None))
        if args.bundle_cap:
            jobs.append(("bundle-mcp", tuple(json.dumps(c) for c in calls), None))
        if len(picked) >= 2:
            jobs.append(("api", (queries[0], picked[0], picked[1]), None))
            if args.bundle_cap:
                jobs.append(("bundle-api", (queries[0], picked[0], picked[1]), None))

    def run(job):
        verb, query, top = job
        try:
            if verb == "mcp":
                return job, arm.compare_mcp([json.loads(c) for c in query])
            if verb == "bundle-mcp":
                return job, arm.compare_bundle_mcp([json.loads(c) for c in query])
            if verb == "api":
                return job, arm.compare_api(*query)
            if verb == "bundle-api":
                return job, arm.compare_bundle_api(*query)
            if verb == "bundle":
                return job, arm.compare_bundle(query[0], query[1], top)
            if top is None:
                return job, arm.compare_verb(verb, query, tunable=verb != "explain")
            fn = arm.compare_find if verb == "find" else arm.compare_ask
            return job, fn(query, top)
        except Exception as exc:  # a reader that crashes is a discordance
            return job, [f"{verb} {query!r} top={top}: {type(exc).__name__}: {exc}"]

    # 🔴 **Windows decodes a pipe with the ANSI code page unless told not to**
    # (2026-09-13, this file's first CI run). `text=True` alone decoded Node's
    # UTF-8 stdout as cp1252, so every title carrying an em dash came back
    # mojibake and the arm reported 174 transcription defects that were not
    # there — a harness artifact in exactly the shape of a real finding. The
    # subprocess calls now name `encoding="utf-8"`, and stdout is reconfigured
    # here because printing the report's own `⚠` to a cp1252 console raises
    # UnicodeEncodeError and kills the run after the comparison has passed.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):  # pragma: no cover - not a tty we own
            pass

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        # Order is restored by `jobs`, not by completion — a parallel harness
        # whose output moves between runs is not reproducible (L3).
        results = list(pool.map(run, jobs))

    bad = [(job, rows) for job, rows in results if rows]
    print(f"discordant: {len(bad)} of {len(results)}")
    for job, rows in bad[:25]:
        for row in rows[:4]:
            print("  ", row)

    if args.evidence:
        # JSONL, one object per query per verb per depth — the shape
        # `tests/test_regression_runs.py` looks for, and the shape SR-RS
        # decision 14 needs: a discordant count is derivable from these rows
        # and from nothing else.
        args.evidence.mkdir(parents=True, exist_ok=True)
        suffix = "contract" if use_tune else "transcription"
        out = args.evidence / f"node-arm-{label}-{suffix}.jsonl"
        condition = {
            "_condition": {
                "corpus": str(root), "rung": args.rung, "arm": suffix,
                "tune_vs_defaults": tune_delta(root), "queries": source,
                "node_entry": str(NODE_ENTRY),
            }
        }
        with out.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps(condition) + "\n")
            for (verb, query, top), rows in results:
                fh.write(json.dumps({
                    "rung": label, "verb": verb, "top": top,
                    "query": query if isinstance(query, str) else list(query),
                    "status": "discordant" if rows else "pass",
                    "discordances": len(rows), "detail": rows[:4],
                }) + "\n")
        print(f"evidence : {out} ({len(results)} rows)")

    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
