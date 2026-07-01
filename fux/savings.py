"""`fux savings` — estimate the token- and dollar-cost win of Fux ($0, deterministic, plan §12).

Turns the plan's *illustrative* cost table into **measured** numbers from this
project's real file sizes. No LLM, no network — just byte counts and a transparent
≈4-chars/token heuristic, priced in **dollars** at a configurable `usd_per_mtok`
(default = Claude Opus 4.8's input rate; the win is on input tokens). Two framings:

* **Per lookup** (optionally for a query) — answering a question about some
  governed logic costs, without Fux, a read of the governed source file(s); with
  Fux, the Tier-1 INDEX (injected once per session) plus the one Tier-2 rule.
* **Aggregate** — the same comparison averaged over every documented topic (a rule
  that carries `code_refs`).

Estimates, not invoices: "without Fux" assumes you read the whole governed file
because you don't yet know the lines; "with Fux" assumes the rule points you
straight to them. Both sides use the same token heuristic, so the *ratio* is the
honest signal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fux import config, index, loader, paths, recall
from fux.model import Rule, RuleSet

CHARS_PER_TOKEN = 4  # rough, model-agnostic; applied identically to both sides
DEFAULT_USD_PER_MTOK = 5.0  # $/million input tokens — Claude Opus 4.8 input price (config: usd_per_mtok)


def tok(text: str) -> int:
    return round(len(text) / CHARS_PER_TOKEN)


def usd(tokens: float, per_mtok: float = DEFAULT_USD_PER_MTOK) -> float:
    """Dollar cost of `tokens` at `per_mtok` $/million tokens — the savings is on
    *input* tokens (a small rule read instead of the whole governed file)."""
    return tokens / 1_000_000 * per_mtok


def fmt_usd(amount: float) -> str:
    """Compact dollar string: cents precision once past a cent, 4 dp below it."""
    return f"${amount:,.2f}" if abs(amount) >= 1 else f"${amount:.4f}"


def _read_tokens(p: Path) -> int:
    try:
        return tok(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return 0


def _ref_file(ref: str) -> str:
    """The file part of a `code_ref` (strip a `#Lx-Ly` range and trailing slash)."""
    return ref.split("#", 1)[0].strip().rstrip("/")


def rule_tokens(r: Rule) -> int:
    """Tier-2 cost: what Claude opens when it reads the rule (the source file)."""
    return _read_tokens(r.path)


def governed(root: Path, r: Rule) -> tuple[int, int, int]:
    """(tokens, files_counted, files_missing) for the distinct files a rule governs."""
    counted, missing, seen = 0, 0, set()
    for ref in r.code_refs:
        rel = _ref_file(ref)
        if not rel or rel in seen:
            continue
        seen.add(rel)
        p = root / rel
        if p.is_file():
            counted += _read_tokens(p)
        else:
            missing += 1
    return counted, len(seen) - missing, missing


@dataclass
class Lookup:
    query: str
    rules: list[Rule]
    index_tok: int
    with_first: int          # INDEX (once) + matched rules
    with_later: int          # matched rules only (INDEX already in context)
    without: int             # whole governed file(s)
    missing: int = 0

    def ratio_first(self) -> float:
        return self.without / self.with_first if self.with_first else 0.0

    def ratio_later(self) -> float:
        return self.without / self.with_later if self.with_later else 0.0


@dataclass
class Report:
    n_rules: int
    index_tok: int
    governed_tok: int
    governed_files: int
    topics: int              # rules with at least one existing governed file
    avg_without: float
    avg_rule: float
    usd_per_mtok: float = DEFAULT_USD_PER_MTOK
    lookup: Lookup | None = None
    notes: list[str] = field(default_factory=list)

    def avg_ratio(self) -> float:
        return self.avg_without / self.avg_rule if self.avg_rule else 0.0


def _ruleset(root: Path) -> tuple[RuleSet, int, dict]:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    return rs, tok(index.render_index(rs)), cfg


def build(root: Path, query: str | None = None, top: int = 3) -> Report:
    rs, index_tok, cfg = _ruleset(root)
    active = rs.active()

    gov_tok = gov_files = topics = 0
    sum_without = sum_rule = 0
    seen_files: set[str] = set()
    for r in active:
        counted, nfiles, _missing = governed(root, r)
        for ref in r.code_refs:                       # distinct-file corpus total
            rel = _ref_file(ref)
            if rel and rel not in seen_files and (root / rel).is_file():
                seen_files.add(rel)
                gov_tok += _read_tokens(root / rel)
                gov_files += 1
        if counted > 0:                               # a measurable "topic"
            topics += 1
            sum_without += counted
            sum_rule += rule_tokens(r)

    report = Report(
        n_rules=len(active), index_tok=index_tok,
        governed_tok=gov_tok, governed_files=gov_files, topics=topics,
        avg_without=(sum_without / topics) if topics else 0.0,
        avg_rule=(sum_rule / topics) if topics else 0.0,
        usd_per_mtok=float(cfg.get("usd_per_mtok", DEFAULT_USD_PER_MTOK)),
    )
    if topics == 0:
        report.notes.append("No active rule carries an existing `code_refs` file, "
                            "so a code-read baseline can't be measured yet.")
    if query:
        report.lookup = _lookup(root, query, index_tok, top)
    return report


def _lookup(root: Path, query: str, index_tok: int, top: int) -> Lookup:
    matched = [r for r, _ in recall.run(root, query, top=top)]
    rules_tok = sum(rule_tokens(r) for r in matched)
    without = missing = 0
    seen: set[str] = set()
    for r in matched:
        for ref in r.code_refs:
            rel = _ref_file(ref)
            if not rel or rel in seen:
                continue
            seen.add(rel)
            if (root / rel).is_file():
                without += _read_tokens(root / rel)
            else:
                missing += 1
    return Lookup(query=query, rules=matched, index_tok=index_tok,
                  with_first=index_tok + rules_tok, with_later=rules_tok,
                  without=without, missing=missing)


def render(rep: Report) -> str:
    price = rep.usd_per_mtok
    money = lambda t: fmt_usd(usd(t, price))  # noqa: E731 — local shorthand
    L = [f"fux savings — cost estimate ($0, heuristic ≈{CHARS_PER_TOKEN} chars/token · "
         f"${price:,.2f}/M input tok)", ""]
    L.append("Corpus")
    L.append(f"  active rules:        {rep.n_rules}")
    L.append(f"  INDEX (Tier-1):      {rep.index_tok:>8,} tok  ≈ {money(rep.index_tok):>9}   ← injected once per session")
    if rep.topics:
        L.append(f"  avg rule (Tier-2):   {rep.avg_rule:>8,.0f} tok  ≈ {money(rep.avg_rule):>9}   ← opened only when relevant")
    L.append(f"  governed code:       {rep.governed_tok:>8,} tok  ≈ {money(rep.governed_tok):>9}   across {rep.governed_files} files")
    L.append("")

    if rep.lookup is not None:
        lk = rep.lookup
        ids = ", ".join(r.id for r in lk.rules) or "(no rule matched)"
        saved = lk.without - lk.with_later
        L.append(f'Per lookup — "{lk.query}"')
        L.append(f"  matched rules:       {ids}")
        L.append(f"  without Fux:         {lk.without:>8,} tok  ≈ {money(lk.without):>9}   (read governed file(s))")
        L.append(f"  with Fux (1st):      {lk.with_first:>8,} tok  ≈ {money(lk.with_first):>9}   → {_compare(lk.without, lk.with_first)}")
        L.append(f"  with Fux (later):    {lk.with_later:>8,} tok  ≈ {money(lk.with_later):>9}   → {_compare(lk.without, lk.with_later)} "
                 f"(INDEX already in context)")
        L.append("  " + _delta("you save (later)", "you spend (later)", saved, money) + "   per repeat lookup")
        if lk.missing:
            L.append(f"  · {lk.missing} referenced file(s) missing — excluded from the baseline")
        L.append("")

    if rep.topics:
        avg_saved = rep.avg_without - rep.avg_rule
        L.append(f"Across {rep.topics} documented topic(s), per lookup (avg)")
        L.append(f"  without Fux:         {rep.avg_without:>8,.0f} tok  ≈ {money(rep.avg_without):>9}")
        L.append(f"  with Fux (later):    {rep.avg_rule:>8,.0f} tok  ≈ {money(rep.avg_rule):>9}   → {_compare(rep.avg_without, rep.avg_rule)}")
        L.append("  " + _delta("you save (avg)", "you spend (avg)", avg_saved, money))
    for n in rep.notes:
        L.append(f"· {n}")
    return "\n".join(L)


def _x(ratio: float) -> str:
    return f"{ratio:.1f}×" if ratio else "—"


def _compare(without: float, with_tok: float) -> str:
    """Direction-honest comparison: `cheaper` only when Fux actually costs less.

    On a tiny corpus Fux's per-lookup overhead can exceed reading the file, so the
    ratio is < 1 — reporting that as `cheaper` (or `you save: -N`) was a real
    labelling bug (fux-lab Cycle 2). The win grows with codebase size."""
    if not with_tok or not without:
        return "—"
    if with_tok <= without:
        return f"{without / with_tok:.1f}× cheaper"
    return f"{with_tok / without:.1f}× costlier"


def _delta(save_label: str, spend_label: str, saved: float, money) -> str:
    """`you save: N` when saved ≥ 0, else `you spend: N extra` (never a negative save)."""
    if saved >= 0:
        return f"{save_label}:    {saved:>8,.0f} tok  ≈ {money(saved):>9}"
    return f"{spend_label}:   {-saved:>8,.0f} tok  ≈ {money(-saved):>9}   extra"
