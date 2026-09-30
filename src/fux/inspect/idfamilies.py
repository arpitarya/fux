"""The identifier lens: which ID families a corpus writes (W-233, compare doc S8).

**Read-only, as every lens is** (SR-INSPECT). It names families and the lever
that would act on them — `fux identifiers --write` — and applies nothing. The
verb that writes `.fux/identifiers.toml [detected]` calls `detect` and nothing
else, so what the report proposes and what the verb writes are one function.

**Deterministic (L4).** No model, no sampling: every indexed document's text is
read from disk (never fetched, L5) through the same decode path `refer` uses,
every raw analyzer token is considered, and the output is sorted.

## The rule

1. **A candidate** is a raw analyzer token that starts with a letter, carries a
   digit and a `-` or `_`, and is not a path (`/`), a file name (`.md`), a
   decimal or version (`0.5`, `2.3.1`) or a same-prefix range (`L0-L12`).
2. It is cut into **segments**: letter runs, digit runs, separators.
3. Tokens are grouped by **the first letter run, case-folded, plus the kinds of
   every later segment** — spaCy's `shape_`, with the prefix kept literal. The
   [fixture](../../../work/regression/2026-09-28-identifier-fixture/report.md)
   measured why the prefix must be literal: by shape alone the four largest
   "families" on rung-10000 were dates, decimals, link paths and `400/hour`.
4. **The template:** the prefix as most often written; a later letter run stays
   literal when every member shares it (`NRL-HSE-{n}`), else `{X}`; a digit run
   is always `{n}`; `-`/`_` as most often written (`-` on a tie); `.` literal.
5. A family **qualifies** at ≥ `min_values` distinct values across ≥ `min_docs`
   documents (`.fux/inspect.toml [identifiers]`), and only if its template
   parses under the grammar `.fux/identifiers.toml` enforces.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..query.analyzer import _WORD_RE
from ..query.identifiers import parse_template
from ..errors import FuxError

_SEGMENT = re.compile(r"[A-Za-z]+|[0-9]+|[-_.]")


@dataclass(frozen=True)
class Family:
    template: str
    values: int
    docs: int
    examples: tuple[str, ...]


@dataclass
class Detection:
    families: list[Family] = field(default_factory=list)
    documents: int = 0
    candidates: int = 0


def _segments(token: str) -> list[str] | None:
    segs = _SEGMENT.findall(token)
    if "".join(segs) != token:
        return None
    return segs


#: A token that is a FILE NAME (`W-104-enrich.md`, `A-t100.jsonl`): its last
#: `.` is followed by letters only.
_FILE_NAME = re.compile(r"\.[A-Za-z]+$")
#: A decimal or a version inside the token (`anchor-0.5`, `v2.3.1`): a number,
#: not an identifier's shape.
_DECIMAL = re.compile(r"[0-9]\.[0-9]")
#: A RANGE written with one prefix twice (`L0-L12`, `D1-D18`).
_RANGE = re.compile(r"^([A-Za-z]+)[0-9]+[-_]\1[0-9]+$", re.IGNORECASE)


def _is_candidate(token: str) -> bool:
    """Rule 1. Found on fux's own prose, not on the ladder (whose IDs are all
    uppercase codes): a `.` alone made section numbers (`A.13`) and parameter
    values (`alpha.0`) into families, file names became slug families, and
    `L0-L12` became `L{n}-L{n}`. So a `-` or `_` is required, and a file name,
    a decimal and a same-prefix range are not identifiers."""
    return (
        token[0].isascii() and token[0].isalpha()
        and "/" not in token
        and any(c.isdigit() for c in token)
        and any(c in "-_" for c in token)
        and not _FILE_NAME.search(token)
        and not _DECIMAL.search(token)
        and not _RANGE.match(token)
    )


def _kind(seg: str) -> str:
    if seg[0].isalpha():
        return "a"
    if seg[0].isdigit():
        return "d"
    return seg


def _template(members: list[list[str]]) -> str:
    """Rule 4. `members` are the segment lists of one family's distinct values."""
    first = Counter(m[0] for m in members)
    prefix = min(first, key=lambda p: (-first[p], p))
    out = [prefix]
    for i in range(1, len(members[0])):
        column = [m[i] for m in members]
        kind = _kind(column[0])
        if kind == "d":
            out.append("{n}")
        elif kind == "a":
            folded = {c.lower() for c in column}
            if len(folded) == 1:
                spelled = Counter(column)
                out.append(min(spelled, key=lambda p: (-spelled[p], p)))
            else:
                out.append("{X}")
        elif kind in "-_":
            seps = Counter(c for c in column if c in "-_")
            out.append("-" if seps["-"] >= seps["_"] else "_")
        else:
            out.append(kind)
    return "".join(out)


def detect(texts, *, min_values: int, min_docs: int, examples: int) -> Detection:
    """`texts` yields `(doc_id, text)`. Returns the qualifying families, sorted."""
    values: dict[tuple, dict[str, list[str]]] = defaultdict(dict)
    docs: dict[tuple, set[str]] = defaultdict(set)
    out = Detection()
    for doc_id, text in texts:
        out.documents += 1
        for raw in _WORD_RE.findall(text):
            if not _is_candidate(raw):
                continue
            segs = _segments(raw)
            if segs is None:
                continue
            out.candidates += 1
            key = (segs[0].lower(), tuple(_kind(s) for s in segs[1:]))
            values[key].setdefault(raw.lower(), segs)
            docs[key].add(doc_id)
    for key in sorted(values):
        vals = values[key]
        if len(vals) < min_values or len(docs[key]) < min_docs:
            continue
        members = [vals[v] for v in sorted(vals)]
        template = _template(members)
        try:
            parse_template(template)
        except FuxError:
            continue
        out.families.append(Family(
            template=template,
            values=len(vals),
            docs=len(docs[key]),
            examples=tuple("".join(m) for m in members[:examples]),
        ))
    out.families.sort(key=lambda f: f.template)
    return out


def corpus_texts(root: Path, view, *, tick=None):
    """`(doc_id, text)` for every indexed document whose bytes are on this disk.

    `tick(loc)` is called once per indexed document, readable or not — the
    progress count (W-238) is of the index, not of what this disk still holds.
    """
    from .facts import readable_text, source_bytes

    for doc in view.docs:
        if tick is not None:
            tick(doc.loc)
        raw = source_bytes(root, doc.id, doc.loc)
        if raw is None:
            continue
        text, _ = readable_text(root, doc.id, doc.loc, raw)
        yield doc.id, text


def identifier_families(root: Path, view, *, examples: int, progress=None) -> Detection:
    """The lens: `detect` over the indexed corpus, at `inspect.toml`'s floors.

    It re-reads and re-decodes every document, which is why `fux identifiers`
    and `fux doctor` show a `detect` bar (W-238) when handed a `progress`.
    """
    from ..progress import NULL as _NULL_PROGRESS

    progress = progress or _NULL_PROGRESS
    with progress.phase("detect", len(view.docs)) as p:
        return detect(
            corpus_texts(root, view, tick=lambda loc: p.update(1, detail=loc)),
            min_values=view.config.min_values,
            min_docs=view.config.min_docs,
            examples=examples,
        )


# ---- regex parity (F3) --------------------------------------------------------

#: The Node side of the parity check: the SAME compiled source, run by V8 over
#: the same texts. Flags "gi" are Python's `re.ASCII | re.IGNORECASE`'s twin for
#: the ASCII classes the guard admits.
_NODE_SPANS = (
    "let s='';process.stdin.on('data',d=>s+=d).on('end',()=>{"
    "const {source,texts}=JSON.parse(s);const rx=new RegExp(source,'gi');"
    "process.stdout.write(JSON.stringify(texts.map(t=>{const o=[];rx.lastIndex=0;let m;"
    "while((m=rx.exec(t))!==null){o.push([m.index,m.index+m[0].length]);}return o;})));});"
)


@dataclass(frozen=True)
class Parity:
    """Did Python `re` and V8 find the same spans? `diff` names the first miss."""

    ran: bool
    agree: bool
    documents: int
    matches: int
    diff: str = ""


def _utf16(text: str, offset: int) -> int:
    """A code-point offset as the UTF-16 offset V8 reports for it."""
    return len(text[:offset].encode("utf-16-le")) // 2


def regex_parity(rules, texts: list[tuple[str, str]]) -> Parity:
    """Run `rules`' combined matcher in Python and in `node` over `texts`.

    Needs only `node` on PATH — not the vendored reader — because what differs
    between the readers is the regex ENGINE, and the source both compile is the
    one `rules.combined_source()` returns. Canonical forms are not compared
    here: the shared fixture holds them equal in the engine's own tests.
    """
    import json
    import shutil
    import subprocess

    from ..query.identifiers import _compiled

    node = shutil.which("node")
    if node is None or not rules.rules:
        return Parity(ran=False, agree=True, documents=len(texts), matches=0)
    rx, _groups, _gated = _compiled(rules)  # the combined scan: what Node runs
    py = [[(_utf16(t, m.start()), _utf16(t, m.end())) for m in rx.finditer(t)] for _, t in texts]
    out = subprocess.run(
        [node, "-e", _NODE_SPANS],
        input=json.dumps({"source": rules.combined_source(), "texts": [t for _, t in texts]}),
        capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode:
        return Parity(ran=True, agree=False, documents=len(texts), matches=0,
                      diff=f"node refused the pattern: {out.stderr.strip().splitlines()[-1][:160]}")
    js = [[tuple(span) for span in row] for row in json.loads(out.stdout)]
    matches = sum(len(row) for row in py)
    for (doc_id, text), a, b in zip(texts, py, js):
        if a != b:
            only = sorted(set(a) ^ set(b))[:1]
            where = f" near {ascii(text.encode('utf-16-le')[only[0][0] * 2:only[0][1] * 2].decode('utf-16-le'))}" if only else ""
            return Parity(ran=True, agree=False, documents=len(texts), matches=matches,
                          diff=f"{doc_id}: Python found {len(a)} match(es), Node {len(b)}{where}")
    return Parity(ran=True, agree=True, documents=len(texts), matches=matches)


# ---- the test bench (`fux serve`'s Identifiers tab, F3) ------------------------


def bench(texts: list[tuple[str, str]], pattern: str, kind: str, *, examples: int, parity_docs: int) -> dict:
    """Everything the Identifiers tab shows for one typed template or regex.

    **Read-only** (SR-SERVE): it compiles the pattern exactly as
    `.fux/identifiers.toml` would, runs it over the corpus, and returns the line
    to paste — it writes no byte. A refused pattern returns the refusal, which
    is the same sentence `fux ingest` would stop on.
    """
    import json

    from ..query.analyzer import analyze
    from ..query.identifiers import IdentifierRules, parse_regex, parse_template

    try:
        rule = parse_template(pattern) if kind == "template" else parse_regex(pattern)
    except FuxError as exc:
        return {"pattern": pattern, "kind": kind, "refused": str(exc)}
    rules = IdentifierRules(rules=(rule,))
    total = 0
    docs: list[str] = []
    shown: list[dict] = []
    for doc_id, text in texts:
        found = rules.matches(text)
        if not found:
            continue
        total += len(found)
        docs.append(doc_id)
        for s, e, canon in found:
            if len(shown) < examples and all(x["surface"] != text[s:e] for x in shown):
                surface = text[s:e]
                shown.append({
                    "doc": doc_id, "surface": surface, "canonical": canon,
                    "v3": analyze(surface), "with_family": analyze(surface, rules),
                })
    parity = regex_parity(rules, texts[:parity_docs])
    key = "keep" if kind == "template" else "regex"
    return {
        "pattern": pattern,
        "kind": kind,
        "matches": total,
        "documents": len(docs),
        "examples": shown,
        "parity": parity.__dict__,
        "toml": f"{key} = [{json.dumps(pattern)}]   # in [user]",
    }

