---
type: Pointer
description: "One line: the current state and the immediate next step. Overwritten every session."
---

✓ 2026-09-14 Claude Code: **npm publishes directly now — and the reason is that the human gate was never walked through.** `2.0.0` staged 2026-09-13, `2.0.1` staged 2026-09-14, **neither ever approved**, so npm's `latest` has pointed at `2.0.0-alpha.7` (2026-09-02) through two releases while PyPI moved twice — with every release workflow green, because staging IS its success. Arpit ruled them symmetric: [`publish.yml`](../.github/workflows/publish.yml) runs `npm publish`, [SR-WORK-RELEASE](../records/0063_WORK-release.md) decision 8 rewritten (8a added) and [SR-NODE-SEARCH](../records/0153_node-search.md) decision 14 amended. `main` `52b78405` CI 8/8 + node-arm green, merged here. ⚠ **A release precondition now lives OUTSIDE this repo and cannot be asserted from it:** `Allow npm publish` must stay ticked on the `fux-engine` trusted publisher at npmjs.com. 🔴 **`2.0.1` IS STILL NOT ON npm** — the switch reaches the NEXT release; the two staged versions are cleared by hand or superseded by a `2.0.2`. Also: `test_sr_ownership` now ignores a bytecode-only directory (two strikes, [SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13). 🔴 `work/BLOCKED.json` open. Seven 🔴 on Arpit: W-156, W-146, W-112, W-144, W-148, W-175, W-170.

→ **Next:** clear the two staged npm versions — approve them, or cut `2.0.2` so the new path proves itself on a real release. Until then npm serves an alpha.
