"""`.fux/inspect.toml` — what `fux inspect` calls a finding, how much it samples,
and how many rows it shows (W-225 stage 4c; SR-LAW-12 decision 1, R6).

Every value the lenses read lives in the file; the packaged template is its one
home. **Inside a repository the file is required**, and a missing file or key
is a hard error naming it, with the `fux doctor --fix` remedy. **Outside one**
— `fux inspect --diff A B` needs no repository — the template itself is read,
the precedent `.fux/output.toml` set for a run outside a repo.

Nothing here reaches the index or a ranking: a changed threshold changes only
what the report SAYS, which is why these are not `tune.toml` keys.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from importlib import resources
from pathlib import Path

from ..constants import fixed
from ..errors import FuxError

__all__ = ["InspectConfig", "load", "template_text", "INSPECT_NAME"]

INSPECT_NAME = fixed("files", "inspect")

#: What a missing key's error tells the reader to do — `tune.py`'s sentence.
_FIX_HINT = "`fux doctor --fix` writes every missing key from the template `fux setup` uses"


@dataclass(frozen=True)
class InspectConfig:
    """Every `.fux/inspect.toml` value, by `table.key` → field name."""

    boilerplate_df_share: float
    distinctive_df_share: float
    near_duplicate_jaccard: float
    link_target_share: float
    signature_size: int
    band_rows: int
    fingerprint_terms: int
    findable_rank: int
    retrieval_sample: int
    probe_rank: int
    probe_sample: int
    top: int
    lengths_top: int
    passages_cap: int
    words: int
    triage_rows: int
    words_page: int
    words_page_max: int
    skeleton_jaccard: float
    core_share: float
    misfit_floor: float
    length_edges: tuple[int, ...]
    min_values: int
    min_docs: int
    parity_sample: int
    unreachable_share: float
    boilerplate_share: float
    near_duplicate_share: float


#: `field -> (table, kind)`. `share` is a number in (0, 1]; `count` a whole number
#: >= 1; `edges` a non-empty, strictly increasing list of whole numbers >= 1.
_SCHEMA: dict[str, tuple[str, str]] = {
    "skeleton_jaccard": ("families", "share"),
    "core_share": ("families", "share"),
    "misfit_floor": ("families", "share"),
    "length_edges": ("families", "edges"),
    "boilerplate_df_share": ("thresholds", "share"),
    "distinctive_df_share": ("thresholds", "share"),
    "near_duplicate_jaccard": ("thresholds", "share"),
    "link_target_share": ("thresholds", "share"),
    "signature_size": ("minhash", "count"),
    "band_rows": ("minhash", "count"),
    "fingerprint_terms": ("findability", "count"),
    "findable_rank": ("findability", "count"),
    "retrieval_sample": ("findability", "count"),
    "probe_rank": ("probes", "count"),
    "probe_sample": ("probes", "count"),
    "top": ("report", "count"),
    "lengths_top": ("report", "count"),
    "passages_cap": ("xray", "count"),
    "words": ("xray", "count"),
    "triage_rows": ("serve", "count"),
    "words_page": ("serve", "count"),
    "words_page_max": ("serve", "count"),
    "min_values": ("identifiers", "count"),
    "min_docs": ("identifiers", "count"),
    "parity_sample": ("identifiers", "count"),
    "unreachable_share": ("floors", "share"),
    "boilerplate_share": ("floors", "share"),
    "near_duplicate_share": ("floors", "share"),
}
assert set(_SCHEMA) == {f.name for f in fields(InspectConfig)}


def template_text() -> str:
    """The packaged `inspect.toml` — `fux setup`'s file, and a no-repo run's values."""
    return (resources.files("fux") / "templates" / fixed("templates", "inspect")).read_text(
        encoding="utf-8"
    )


def load(root: Path | None) -> InspectConfig:
    """The repository's `.fux/inspect.toml`, strictly; the template when `root` is None."""
    if root is None:
        return _parse(template_text(), "the packaged inspect.toml template")
    path = root / INSPECT_NAME
    if not path.is_file():
        raise FuxError(
            f"{path} is missing - `fux setup` writes it, and `fux doctor --fix` restores a "
            "deleted one. fux holds no copy of its values in code"
        )
    return _parse(path.read_bytes().decode("utf-8-sig"), str(path))


def _parse(text: str, label: str) -> InspectConfig:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise FuxError(f"{label}: invalid TOML ({exc})") from exc
    known_tables = {table for table, _ in _SCHEMA.values()}
    errors: list[str] = []
    for table in sorted(set(data) - known_tables):
        errors.append(f"[{table}] is not an inspect.toml table - known: {', '.join(sorted(known_tables))}")
    values: dict[str, object] = {}
    missing = False
    for name, (table, kind) in _SCHEMA.items():
        node = data.get(table, {})
        if name not in node:
            errors.append(f"[{table}] {name} is missing")
            missing = True
            continue
        value = node[name]
        if kind == "edges":
            ok = (
                isinstance(value, list) and value
                and all(isinstance(v, int) and not isinstance(v, bool) and v >= 1 for v in value)
                and all(a < b for a, b in zip(value, value[1:]))
            )
            if not ok:
                errors.append(f"[{table}] {name} must be a strictly increasing list of whole numbers >= 1 (got {value!r})")
            else:
                value = tuple(value)
        elif kind == "count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                errors.append(f"[{table}] {name} must be a whole number >= 1 (got {value!r})")
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1:
            errors.append(f"[{table}] {name} must be a share in (0, 1] (got {value!r})")
        values[name] = value
    for table in known_tables & set(data):
        extra = sorted(k for k in data[table] if k not in _SCHEMA or _SCHEMA[k][0] != table)
        errors += [f"[{table}] {k} is not a key" for k in extra]
    if errors:
        tail = f"\n  {_FIX_HINT}" if missing else ""
        raise FuxError(f"{label}:\n  " + "\n  ".join(errors) + tail)
    return InspectConfig(**values)
