"""`fux llms` — an llms.txt, or an llms-full.txt, rendered from the index. W-284.

**What it is.** [llms.txt](https://llmstxt.org/) is a Markdown map of a
project for a language model: one H1, a blockquote, then H2 sections of
`- [name](url): notes` lists, with a section titled `Optional` that a reader
may skip when context is short. `llms-full.txt` is the convention — not part
of the spec — of the same map followed by the documents' text.

**What fux contributes is the selection, never a copy**
([SR-LLMS](../../records/0162_llms.md)):

- **The index decides which documents and their titles** — every indexed
  document under the `--in` prefixes, sorted by `loc` (L4). Archived documents
  go under `## Optional`; they are history, which is what that section is for.
- **The notes on a link are the document's own `description:`**, read from the
  file's frontmatter at render time — the owner's words, fetched from the
  owner, exactly as the refer plane reads a span.
- **`--full` reads each prose document off disk to stdout.** A URL document is
  listed and never fetched (L5), and a document a non-prose decoder reads
  (HTML, a spreadsheet, an SVG) is listed and not inlined: its bytes are not
  text a model should read as written.
- 🔴 **stdout only.** fux writes no file, so nothing about the corpus becomes
  durable outside its source by fux's hand (L3). Where the operator redirects
  it is the operator's decision.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import quote, urlparse

from .constants import fixed
from .errors import FuxError

_OPTIONAL = fixed("llms", "optional_section")
_ROOT_SECTION = fixed("llms", "root_section")
_RULE = fixed("llms", "separator")
_SOURCE = fixed("llms", "source_label")


def _prose_locs(root: Path) -> set[str]:
    """The locs the committed register says the prose decoder read.

    Read off `.fux/index/REGISTER` by path rather than through the writer's
    module, which a reader-only install does not have (the layer map).
    """
    from .acquire.ingestlog import PROSE

    path = root / fixed("index", "dir") / fixed("register", "file")
    if not path.is_file():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        loc, _sha, decoder, *_tail = line.split("\t")
        if decoder == PROSE:
            out.add(loc)
    return out


def _description(root: Path, loc: str) -> str:
    """The document's own `description:` frontmatter, one line, or `""`."""
    from .frontmatter import parse

    path = root / loc
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    value = parse(text).meta.get("description")
    return " ".join(str(value).split()) if value else ""


def _section(record: dict) -> str:
    """A file's top-level folder (root files: `root_section`); a URL's host."""
    if record["id"].startswith("url:"):
        return urlparse(record["loc"]).netloc or record["loc"]
    head, sep, _rest = record["loc"].partition("/")
    return head if sep else _ROOT_SECTION


def _link(loc: str, doc_id: str, base: str) -> str:
    if doc_id.startswith("url:"):
        return loc
    return base + quote(loc)


def select(records: dict, prefixes: list[str]) -> list[dict]:
    """The records under any of `prefixes` (all when none), sorted by `loc`."""
    chosen = [
        r for r in records.values()
        if not prefixes or any(r["loc"] == p or r["loc"].startswith(p) for p in prefixes)
    ]
    return sorted(chosen, key=lambda r: r["loc"])


def render(
    root: Path, records: dict, *, prefixes: list[str], title: str, summary: str, base: str, full: bool
) -> str:
    """The whole document, deterministic in the index and the working tree."""
    chosen = select(records, prefixes)
    if not chosen:
        raise FuxError("no indexed document matches the --in prefixes given")
    current = [r for r in chosen if not r.get("archived")]
    archived = [r for r in chosen if r.get("archived")]

    out = [f"# {title}", ""]
    if summary:
        out += [f"> {summary}", ""]

    sections: dict[str, list[dict]] = {}
    for record in current:
        sections.setdefault(_section(record), []).append(record)
    order = sorted(sections, key=lambda name: (name != _ROOT_SECTION, name))
    for name, rows in [(n, sections[n]) for n in order] + ([(_OPTIONAL, archived)] if archived else []):
        out += [f"## {name}", ""]
        for record in rows:
            line = f"- [{record.get('title') or record['loc']}]({_link(record['loc'], record['id'], base)})"
            note = _description(root, record["loc"]) if record["id"].startswith("file:") else ""
            out.append(f"{line}: {note}" if note else line)
        out.append("")

    if full:
        from .frontmatter import parse

        prose = _prose_locs(root)
        for record in current:
            if not record["id"].startswith("file:") or record["loc"] not in prose:
                continue
            path = root / record["loc"]
            if not path.is_file():
                continue
            # The body, never the frontmatter: its delimiter is the separator's
            # spelling, and its fields are this file's notes, already above.
            body = parse(path.read_text(encoding="utf-8", errors="replace")).body.strip("\n")
            out += [_RULE, ""]
            if not body.startswith("# "):
                out += [f"# {record.get('title') or record['loc']}", ""]
            out += [f"{_SOURCE} {_link(record['loc'], record['id'], base)}", "", body, ""]
    return "\n".join(out).rstrip("\n") + "\n"


def cmd_llms(args) -> int:
    from .config import find_root
    from .store import read_index

    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run `fux llms` from inside a configured repo")
    text = render(
        root,
        read_index(root),
        prefixes=list(args.prefixes or []),
        title=args.title or root.name,
        summary=args.summary or "",
        base=args.base_url or "",
        full=bool(args.full),
    )
    sys.stdout.write(text)
    return 0
