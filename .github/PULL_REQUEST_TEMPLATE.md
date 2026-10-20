## What and why

<!-- One or two sentences: what this changes, and the problem it solves. Link the issue if there is one. -->

## Records

<!-- Name every SR this change amends (records/), or write "no SR affected". A behaviour change lands with its record updated in the same change. -->

## Checklist

- [ ] `uv run pytest -q tests` passes
- [ ] `uv run pytest -q tests_e2e` passes
- [ ] `node --test node/test/*.test.mjs` passes (if `node/` changed)
- [ ] Records amended in this change, or "no SR affected" stated above
- [ ] `CHANGELOG.md` updated under *Unreleased* for a user-visible change
- [ ] No new dependency without an OSI-approved licence (L2)
