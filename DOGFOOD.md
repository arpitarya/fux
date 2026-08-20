# DOGFOOD — fux, used on itself

**Status:** live, ongoing. Not a milestone gate — [W-27](work/IMPLEMENTATION.md)
closed by Arpit's ratification on 2026-08-20, replacing the retired two-week
logged-use gate with one standing obligation: **refresh this file on every fux
version upgrade.**

## Current

- **`v0.33.0`.** `.fux/` in this repo is self-indexed — `fux ask`/`fux find`
  answer against fux's own docs and code, and `fux --version` reports the
  version this file names. That is the dogfood: this repo is a live corpus,
  not a fixture.

## Log

Append one entry per version bump: what broke, what was awkward, what
changed as a result. Empty until the next bump — nothing has been logged yet.
