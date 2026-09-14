"""`fux inspect` — an X-ray of the index: what is on everything, what nothing
can reach, what is duplicated, and what the analyzer never saw.

## The boundary against `fux doctor`, stated once

`doctor` checks the **environment** — is the layout right, are the hooks
wired, is the reader current, is `pii.toml` there. `inspect` checks the
**index** — the thing the environment was set up to produce. Both are
read-only and neither applies a lever. A row belongs in `doctor` when the fix
is a command or a config edit; it belongs here when the fix is a change to the
corpus, and the report says which lever that is.

## What it writes, and what it never writes

Two artifacts, both under **`.fux/runtime/inspect/`**, which is DERIVED and
gitignored: `report.md` and `report.json`, plus the local `dictionary.json`
that names the hashes. **`git status` is clean on a clean clone after a run**,
and `tests_e2e/test_inspect_verb.py` asserts exactly that — the whole point of the
verb is that reading the index tells you about the corpus without adding
anything to it.

**The report names words; the commit never does.** The committed index holds
term hashes ([SR-POSTINGS](../../../records/0112_postings.md) decision 2); the
words come from `dictionary.py`, built locally by re-tokenising the sources
that are already on this disk. Offline (L4), deterministic (L3), nothing new
committed (L2, L8).
"""

from __future__ import annotations

import json as json_mod
from dataclasses import dataclass
from pathlib import Path

from ..errors import FuxError
from . import checks as checks_mod
from . import dictionary as dictionary_mod
from . import lenses as lenses_mod
from ._scan import read_index_view

__all__ = ["Report", "cmd_inspect", "inspect_index", "render_markdown", "as_dict"]

REPORT_NAME = "report.md"
JSON_NAME = "report.json"


@dataclass
class Report:
    view: object
    dictionary: object
    boilerplate: object
    findability: object
    lengths: object
    duplication: object
    coverage: object
    graph: object
    checks: list


def inspect_index(
    root: Path,
    *,
    retrieval_sample: int = lenses_mod.DEFAULT_RETRIEVAL_SAMPLE,
    top: int = 20,
    rebuild_dictionary: bool = False,
    progress=None,
) -> Report:
    """Run every lens over the committed index and return the whole report."""
    view = read_index_view(root, progress=progress)
    if view.n == 0:
        raise FuxError(
            "there is no committed index to inspect. Run `fux ingest` first; "
            "`fux doctor` says whether the layout is ready for it."
        )
    dictionary = dictionary_mod.load_or_build(
        root, view, rebuild=rebuild_dictionary, progress=progress
    )
    boilerplate = lenses_mod.boilerplate(view, dictionary, top=top)
    findability = lenses_mod.findability(
        root, view, dictionary, sample=retrieval_sample, top_lists=top, progress=progress
    )
    lengths = lenses_mod.lengths(view, top_lists=min(top, 10))
    duplication = lenses_mod.duplication(view, top_lists=top)
    coverage = lenses_mod.coverage(root, view, dictionary)
    graph = lenses_mod.graph_shape(view, top_lists=top)
    return Report(
        view=view,
        dictionary=dictionary,
        boilerplate=boilerplate,
        findability=findability,
        lengths=lengths,
        duplication=duplication,
        coverage=coverage,
        graph=graph,
        checks=checks_mod.run_checks(boilerplate, findability, duplication, documents=view.n),
    )


def _share(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f} %"


def _lever(finding: str) -> str:
    return lenses_mod.LEVERS[finding]


def render_markdown(report: Report) -> str:
    """The report, as Markdown. No timestamp anywhere in it, on purpose.

    ⚠ **A wall-clock line would make the file different on every run**, which
    is L3's *byte-identical* guarantee broken by a decoration — and the
    determinism test would have to exclude the one line most likely to hide a
    real change underneath it. The index's own shard shas are the provenance,
    and they are a fact about the input rather than about when someone looked.
    """
    view = report.view
    out: list[str] = []
    add = out.append

    add("# `fux inspect` — the index, as it is\n")
    add(
        f"{view.n} document(s) · {len(view.term_of)} distinct term(s) · "
        f"{view.postings} posting(s) · {len(view.edges)} edge(s)\n"
    )
    add("**Read-only.** Every finding below names the lever that would change it, and applies none.\n")

    add("\n## Checks — four numbers, three of which carry a flag\n")
    add("| check | value | floor | status | what it means |")
    add("|---|---|---|---|---|")
    for check in report.checks:
        floor = check.floor
        bound = (
            "— *(descriptive: no floor separates a healthy corpus from a bad one)*"
            if floor is None
            else floor.describe() + (" *(provisional)*" if floor.provisional else "")
        )
        add(f"| {check.name} | {_share(check.value)} | {bound} | {check.status} | {check.detail} |")
    add(
        "\nEvery floor above is **provisional**: measured on the golden ladder, never tuned to one "
        "repository, and dropped to descriptive if it ever flags a healthy rung. A flag is "
        "*attention*, never a failure — `fux inspect` exits 0 whatever it finds.\n"
    )

    boiler = report.boilerplate
    add("\n## 1 · Boilerplate — what is on everything\n")
    add(
        f"- {boiler.boilerplate_terms} term(s) sit on half the corpus or more, carrying "
        f"{boiler.boilerplate_postings} of {boiler.postings} postings "
        f"(**{_share(boiler.boilerplate_share)}**).\n"
        f"- {boiler.hapax} of {boiler.terms} term(s) are on exactly one document "
        f"(**{_share(boiler.hapax_share)}** hapax).\n"
        f"- Zipf slope `{_number(boiler.zipf_slope)}` (the law predicts about −1) · "
        f"Heaps β `{_number(boiler.heaps_beta)}`, K `{_number(boiler.heaps_k, 1)}`. "
        f"A low β means each new document brings few new words — a corpus of near-copies."
    )
    add(f"\nLever: {_lever('boilerplate term')}\n")
    add("| word | df | share | idf |")
    add("|---|---|---|---|")
    for _hash, word, df, share, idf in boiler.top:
        add(f"| `{word}` | {df} | {share * 100:.0f} % | {idf:.2f} |")

    find = report.findability
    add("\n## 2 · Findability — what no query can reach\n")
    add(
        f"- **{len(find.unfindable)} document(s) carry no distinctive term at all** "
        f"(every term they hold is on more than {view.distinctive_df:.0f} documents). "
        f"This half is EXHAUSTIVE — no retrieval run is needed to know it.\n"
        f"- Retrieval: {find.retrieved} of {find.sampled} document(s) come back in the top "
        f"{lenses_mod.FINDABLE_RANK} for their own {lenses_mod.FINGERPRINT_TERMS} most distinctive "
        f"words"
        + ("." if find.sample_is_whole_corpus else " — an evenly spaced SAMPLE, so the share is an estimate.")
    )
    add(f"\nLever: {_lever('unfindable document')}\n")
    if find.unfindable:
        add("**No distinctive term:**\n")
        for doc_id in find.unfindable[:20]:
            add(f"- `{doc_id}`")
        if len(find.unfindable) > 20:
            add(f"- … {len(find.unfindable) - 20} more")
    if find.misses:
        add("\n**Did not retrieve itself** (rank, or absent):\n")
        for doc_id, rank in find.misses[:20]:
            add(f"- `{doc_id}` — {'absent' if rank is None else f'rank {rank}'}")
        if len(find.misses) > 20:
            add(f"- … {len(find.misses) - 20} more")

    length = report.lengths
    add("\n## 3 · Length and fields\n")
    add("| field | tokens |")
    add("|---|---|")
    for name, total in zip(length.field_names, length.total_flen):
        add(f"| `{name}` | {total} |")
    add("")
    add(f"- Body tokens per document: {_percentile_line(length.body_percentiles)}")
    add(f"- Distinct terms per document: {_percentile_line(length.vocabulary_percentiles)}")
    add(
        f"- {len(length.empty_title)} document(s) have no title tokens · "
        f"{len(length.no_headings)} have no headings · "
        f"{len(length.ctx_over_body)} have more `ctx` than body"
    )
    if length.shortest:
        add("\n**Shortest bodies** — the M1 lesson: a document with a 30-term vocabulary cannot match much.\n")
        for doc_id, tokens in length.shortest:
            add(f"- `{doc_id}` — {tokens} body token(s)")

    dup = report.duplication
    add("\n## 4 · Duplication and templates\n")
    add(
        f"- {dup.pair_count} near-duplicate pair(s) at Jaccard >= "
        f"{lenses_mod.NEAR_DUPLICATE_JACCARD:.2f}, covering {dup.documents_in_a_pair} of {dup.docs} "
        f"document(s) (**{_share(dup.near_duplicate_share)}**).\n"
        f"- {dup.family_count} template family(ies) — documents with an identical heading SET — "
        f"covering {dup.documents_in_a_family} document(s)."
    )
    add(f"\nLever: {_lever('near-duplicate pair')}\n")
    if dup.near_duplicates:
        add("| Jaccard | a | b |")
        add("|---|---|---|")
        for left, right, score in dup.near_duplicates:
            add(f"| {score:.2f} | `{left}` | `{right}` |")
    if dup.families:
        add("\n**Template families:**\n")
        for headings, members in dup.families:
            add(f"- {len(members)} document(s) share `{headings}` — e.g. `{members[0]}`")

    cov = report.coverage
    add("\n## 5 · Analyzer coverage — what the index never saw\n")
    add(
        f"- {cov.kept} of {cov.raw_runs} word-like run(s) in the sources became terms "
        f"(**{_share(cov.kept_share)}** kept; the rest are stopwords).\n"
        f"- {cov.named_terms} of {cov.total_terms} index term(s) are named by the local dictionary "
        f"(**{_share(cov.dictionary_coverage)}**). An unnamed term is one whose document this "
        f"machine cannot read — never a term that does not exist.\n"
        f"- {len(cov.no_content)} document(s) the index knows only by their file name · {len(cov.undecodable)} that no decoder "
        f"could turn into text · {len(cov.unreadable)} whose bytes are not on this disk · "
        f"{len(cov.queued)} already in `.fux/enrich/queue.tsv`."
    )
    add(f"\nLever: {_lever('file-name-only document')}\n")
    for doc_id in cov.no_content[:20]:
        add(f"- `{doc_id}` — no body, heading or `ctx` terms: the index knows only its file name")
    for doc_id, why in cov.unreadable[:20]:
        add(f"- `{doc_id}` — {why}")

    graph = report.graph
    add("\n## 6 · Graph — orphans, hubs, communities\n")
    add(
        f"- {graph.nodes} node(s), {graph.edges} edge(s).\n"
        f"- **{graph.orphan_count} document(s) have no edge at all** — the graph work buys them "
        f"nothing.\n"
        f"- {graph.community_count} community(ies), {graph.singleton_communities} of them a single node."
    )
    add(f"\nLever: {_lever('orphan')}\n")
    if graph.hubs:
        add("| inbound edges | document |")
        add("|---|---|")
        for node, count in graph.hubs:
            add(f"| {count} | `{node}` |")
    if graph.communities:
        add("\n**Community sizes:** " + " · ".join(f"`{label}` {size}" for label, size in graph.communities))

    add("\n---\n")
    add(
        "Provenance: the committed shards this report was built from — "
        + " · ".join(f"`{name}` `{sha[:12]}`" for name, sha in sorted(view.shards.items())[:4])
        + (f" · … {len(view.shards) - 4} more shard(s)" if len(view.shards) > 4 else "")
    )
    return "\n".join(out) + "\n"


def _number(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _percentile_line(percentiles: dict[str, int]) -> str:
    if not percentiles:
        return "n/a"
    return " · ".join(f"{key} {value}" for key, value in percentiles.items())


def as_dict(report: Report) -> dict:
    """`--json`. Sorted keys, no wall clock — the JSON is as reproducible as
    the Markdown, and for the same reason."""
    view = report.view
    boiler = report.boilerplate
    find = report.findability
    length = report.lengths
    dup = report.duplication
    cov = report.coverage
    graph = report.graph
    return {
        "corpus": {
            "documents": view.n,
            "terms": len(view.term_of),
            "postings": view.postings,
            "edges": len(view.edges),
            "shards": dict(sorted(view.shards.items())),
            "boilerplate_df": view.boilerplate_df,
            "distinctive_df": view.distinctive_df,
        },
        "checks": [
            {
                "name": check.name,
                "value": check.value,
                "status": check.status,
                "flagged": check.flagged,
                "floor": None
                if check.floor is None
                else {
                    "bound": check.floor.bound,
                    "direction": check.floor.direction,
                    "provisional": check.floor.provisional,
                    "source": check.floor.source,
                },
                "detail": check.detail,
            }
            for check in report.checks
        ],
        "boilerplate": {
            "terms": boiler.terms,
            "hapax": boiler.hapax,
            "hapax_share": boiler.hapax_share,
            "boilerplate_terms": boiler.boilerplate_terms,
            "boilerplate_postings": boiler.boilerplate_postings,
            "boilerplate_share": boiler.boilerplate_share,
            "zipf_slope": boiler.zipf_slope,
            "heaps_beta": boiler.heaps_beta,
            "heaps_k": boiler.heaps_k,
            "top": [
                {"hash": h, "word": word, "df": df, "share": share, "idf": idf}
                for h, word, df, share, idf in boiler.top
            ],
            "lever": _lever("boilerplate term"),
        },
        "findability": {
            "unfindable": list(find.unfindable),
            "unfindable_count": len(find.unfindable),
            "sampled": find.sampled,
            "retrieved": find.retrieved,
            "sample_is_whole_corpus": find.sample_is_whole_corpus,
            "findable_share": find.findable_share,
            "misses": [{"id": doc_id, "rank": rank} for doc_id, rank in find.misses],
            "fewest_distinctive": [{"id": doc_id, "distinctive": count} for doc_id, count in find.distinctive],
            "lever": _lever("unfindable document"),
        },
        "lengths": {
            "fields": dict(zip(length.field_names, length.total_flen)),
            "body_tokens": length.body_percentiles,
            "distinct_terms": length.vocabulary_percentiles,
            "empty_title": list(length.empty_title),
            "no_headings": list(length.no_headings),
            "ctx_over_body": [
                {"id": doc_id, "ctx": ctx, "body": body} for doc_id, ctx, body in length.ctx_over_body
            ],
            "shortest": [{"id": doc_id, "body_tokens": tokens} for doc_id, tokens in length.shortest],
            "longest": [{"id": doc_id, "body_tokens": tokens} for doc_id, tokens in length.longest],
        },
        "duplication": {
            "pair_count": dup.pair_count,
            "documents_in_a_pair": dup.documents_in_a_pair,
            "near_duplicate_share": dup.near_duplicate_share,
            "near_duplicates": [
                {"a": left, "b": right, "jaccard": score} for left, right, score in dup.near_duplicates
            ],
            "family_count": dup.family_count,
            "documents_in_a_family": dup.documents_in_a_family,
            "families": [{"headings": headings, "members": members} for headings, members in dup.families],
            "lever": _lever("near-duplicate pair"),
        },
        "coverage": {
            "raw_runs": cov.raw_runs,
            "kept": cov.kept,
            "kept_share": cov.kept_share,
            "dictionary_coverage": cov.dictionary_coverage,
            "named_terms": cov.named_terms,
            "total_terms": cov.total_terms,
            "no_content": list(cov.no_content),
            "undecodable": list(cov.undecodable),
            "unreadable": [{"id": doc_id, "why": why} for doc_id, why in cov.unreadable],
            "queued": [{"loc": loc, "why": why} for loc, why in cov.queued],
            "lever": _lever("file-name-only document"),
        },
        "graph": {
            "nodes": graph.nodes,
            "edges": graph.edges,
            "orphan_count": graph.orphan_count,
            "orphans": list(graph.orphans),
            "hubs": [{"id": node, "inbound": count} for node, count in graph.hubs],
            "community_count": graph.community_count,
            "singleton_communities": graph.singleton_communities,
            "communities": [{"label": label, "size": size} for label, size in graph.communities],
            "lever": _lever("orphan"),
        },
        "levers": dict(sorted(lenses_mod.LEVERS.items())),
    }


def cmd_inspect(args) -> int:
    from ..config import find_root

    root = find_root()
    if root is None:
        raise FuxError("not inside a fux repository (no .fux/ found up the tree)")
    progress = getattr(args, "progress", None)
    # `--retrieval-sample` is `default=None` so an absent flag is
    # distinguishable from an explicit `0` (which means *every document*) --
    # the same reason every output-gated flag on this surface defaults to
    # `None`. `0 or default` would silently turn "all of them" into 100.
    sample = getattr(args, "retrieval_sample", None)
    if sample is None:
        sample = lenses_mod.DEFAULT_RETRIEVAL_SAMPLE
    report = inspect_index(
        root,
        retrieval_sample=sample,
        top=getattr(args, "top", 20) or 20,
        rebuild_dictionary=bool(getattr(args, "rebuild_dictionary", False)),
        progress=progress,
    )
    directory = dictionary_mod.inspect_dir(root)
    markdown = render_markdown(report)
    payload = json_mod.dumps(as_dict(report), indent=2, sort_keys=True) + "\n"
    (directory / REPORT_NAME).write_text(markdown, encoding="utf-8")
    (directory / JSON_NAME).write_text(payload, encoding="utf-8")
    if getattr(args, "json", False):
        print(payload, end="")
    else:
        print(markdown, end="")
        rel = (directory / REPORT_NAME).relative_to(root).as_posix()
        print(f"\nWritten to {rel} (gitignored, with its `--json` twin).")
    return 0
