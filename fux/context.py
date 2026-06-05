"""`fux context` — emit the compact INDEX for SessionStart injection (plan §8)."""
from __future__ import annotations

from pathlib import Path

from fux import config, governance, index, loader, paths
from fux.model import RuleSet


def run(root: Path) -> str:
    """Tier-1 index (global ⊕ packs ⊕ project), rebuilt fresh and cheap.

    Decayed `type: memory` entries (past `memory_ttl_days`) are excluded from the
    injection — they stay on disk but stop costing context tokens (plan §17.3).
    """
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    served = None
    if cfg.get("usage_tracking"):
        from fux import usage
        served = usage.last_served(root)
    kept = governance.for_context(rs.rules, cfg, served=served)
    budget = int(cfg.get("context_budget_tokens", 0) or 0)
    if budget > 0:
        from fux import pack          # lazy: knapsack only when a budget is set
        shown = [r for r in kept if r.is_active and r.type != "narrative"]
        kept = pack.select(shown, budget)
    live = RuleSet(rules=kept)
    header = ("<!-- Injected by Fux at SessionStart. This is the Tier-1 INDEX: "
              "open a rule with `fux why <id>` only when relevant. -->\n\n")
    return header + index.render_index(live)
