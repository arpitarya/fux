"""`fux context` — emit the compact INDEX for SessionStart injection (plan §8)."""
from __future__ import annotations

from pathlib import Path

from fux import config, index, loader, paths


def run(root: Path) -> str:
    """Tier-1 index (global ⊕ packs ⊕ project), rebuilt fresh and cheap."""
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    header = ("<!-- Injected by Fux at SessionStart. This is the Tier-1 INDEX: "
              "open a rule with `fux why <id>` only when relevant. -->\n\n")
    return header + index.render_index(rs)
