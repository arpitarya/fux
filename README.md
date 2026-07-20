# Fux

A portable, agent-aware knowledge engine. The *why* behind your code — written as
version-controlled **rules bound to the exact lines they explain**, read by agents
*before* they touch anything, and checked **deterministically** (never by a model)
so a reason can't be silently deleted and can't quietly go stale.

> **Status: rebuild in progress.** The previous implementation is kept for
> reference under [`archive/`](archive/). This tree is a deliberate from-scratch
> rebuild scoped to the rules substrate + the fix loop. See
> [`CLAUDE.md`](CLAUDE.md) and [`docs/fux-plan.md`](docs/fux-plan.md).

## Install (dev)

```bash
uv sync
uv run fux --version
```

## Guarantees

- **`$0`, stdlib-only runtime** — no third-party runtime dependencies.
- **Deterministic** — no model ever sits in the maintenance/enforcement path.
- **Python ≥ 3.11.**

## License

MIT — see [`LICENSE`](LICENSE).
