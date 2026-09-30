"""`fux identifiers [--write]` — propose ID families, and write them on request.

**F1 (Arpit, 2026-09-28): a verb writes `[detected]`.** Without `--write` this
prints what the identifier lens finds and how it differs from the committed
file, and writes nothing. With `--write` it replaces **only the `[detected]`
table** of `.fux/identifiers.toml`; `[user]`, comments and everything else are
kept byte for byte, because `[user]` is the consumer's and wins (F5).

**F2: detection refreshes on demand, never inside `fux ingest`.** A new document
must not change the analyzer for every other document behind the consumer's
back; `fux doctor` says when the families on disk and the ones detected differ.

The family rule itself is [`inspect/idfamilies.py`](inspect/idfamilies.py)'s;
this module calls it and edits one table.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

from .errors import FuxError
from .query import identifiers as ids_mod

#: A TOML table header line — where the `[detected]` block ends.
_TABLE = re.compile(r"^\s*\[[^\[\]]+\]\s*(#.*)?$")


def _detected_block(families) -> str:
    """The `[detected]` table as the verb writes it: the template's own header
    comment, then one line per family with its counts as a trailing comment."""
    template = ids_mod.template_text().splitlines()
    start = next(i for i, line in enumerate(template) if line.strip() == "[detected]")
    head = [line for line in template[start:] if line.startswith("#") or line.strip() == "[detected]"]
    if not families:
        return "\n".join(head + ["families = []"]) + "\n"
    rows = [f'  {json.dumps(f.template)},  # {f.values} values in {f.docs} documents' for f in families]
    return "\n".join(head + ["families = ["] + rows + ["]"]) + "\n"


def rewrite(text: str, families) -> str:
    """`text` with its `[detected]` table replaced (or appended). Pure."""
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.strip().startswith("[detected]")
                  and _TABLE.match(line)), None)
    block = _detected_block(families)
    if start is None:
        sep = "" if text.endswith("\n\n") or not text else ("\n" if text.endswith("\n") else "\n\n")
        return text + sep + block
    end = next((j for j in range(start + 1, len(lines)) if _TABLE.match(lines[j])), len(lines))
    tail = lines[end:]
    return "".join(lines[:start]) + block + ("\n" if tail else "") + "".join(tail)


def _file_detected(root: Path) -> list[str]:
    data = tomllib.loads(ids_mod.path(root).read_bytes().decode("utf-8-sig"))
    return list((data.get("detected") or {}).get("families") or [])


def cmd_identifiers(args) -> int:
    from .config import find_root
    from .inspect._scan import read_index_view
    from .inspect.idfamilies import identifier_families

    root = find_root()
    if root is None:
        raise FuxError("not inside a fux repository (no .fux/ found up the tree)")
    current = ids_mod.load(root)  # a malformed file is refused before anything else
    progress = getattr(args, "progress", None)  # W-238: `read` then `detect`
    view = read_index_view(root, progress=progress)
    if not view.docs:
        raise FuxError("the index is empty — run `fux ingest` first; families are detected "
                       "from the indexed documents")
    detection = identifier_families(root, view, examples=3, progress=progress)
    found = [f.template for f in detection.families]
    on_disk = _file_detected(root)
    new = sorted(set(found) - set(on_disk))
    gone = sorted(set(on_disk) - set(found))

    written = False
    if getattr(args, "write", False) and (new or gone or found != on_disk):
        path = ids_mod.path(root)
        text = path.read_bytes().decode("utf-8-sig")
        updated = rewrite(text, detection.families)
        ids_mod.parse(tomllib.loads(updated), origin=str(path))  # never write a file we would refuse
        path.write_text(updated, encoding="utf-8")
        written = True

    if getattr(args, "json", False):
        print(json.dumps({
            "documents": detection.documents,
            "families": [f.__dict__ | {"examples": list(f.examples)} for f in detection.families],
            "new": new,
            "gone": gone,
            "user": {"rules": [r.source for r in current.rules if r.source not in on_disk]},
            "written": written,
        }, indent=2, sort_keys=True))
        return 0

    out = sys.stdout
    out.write(f"{len(found)} identifier families in {detection.documents} documents\n\n")
    for f in detection.families:
        mark = "+" if f.template in new else " "
        out.write(f" {mark} {f.template:<28} {f.values:>5} values  {f.docs:>5} docs   "
                  f"e.g. {', '.join(f.examples)}\n")
    for t in gone:
        out.write(f" - {t:<28} no longer detected\n")
    out.write("\n")
    if written:
        out.write(f"wrote [detected] in {ids_mod.FILE}: {len(new)} new, {len(gone)} gone. "
                  "Run `fux ingest` to re-analyse the corpus with them.\n")
    elif new or gone:
        out.write(f"{len(new)} new and {len(gone)} gone against {ids_mod.FILE} — "
                  "`fux identifiers --write` writes them; [user] is never touched.\n")
    else:
        out.write(f"{ids_mod.FILE} [detected] is current.\n")
    return 0
