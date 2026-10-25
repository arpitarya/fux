"""`fux pack`'s handler (W-302) -- a package author's verb, so it ships in the
writer layer beside `fux ingest`; the segment writer it calls,
`store/pack.py`, is core."""

from __future__ import annotations

from pathlib import Path

from ..errors import FuxError


def cmd_pack(args) -> int:
    from ..config import find_root
    from ..store import pack

    content = pack.parse_content(args.content)  # before anything reads the repository
    root = find_root()
    if root is None:
        raise FuxError("not inside a fux repository -- there is no index to pack")
    manifest = pack.write_segment(root, Path(args.outdir), content, npm=args.npm, pypi=args.pypi)
    print(f"packed {manifest['docs']} documents into {args.outdir} ({manifest['digest']})")
    return 0
