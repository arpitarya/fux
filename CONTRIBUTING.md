# Contributing to fux

Thanks for helping. **The most useful contribution is a failing query:** the question, the document that should have answered it, and what fux returned instead.

---

## Ways to help

| you have | do this |
|---|---|
| A wrong, missing or stale answer | [Open a wrong-answer issue](https://github.com/arpitarya/fux/issues/new?template=wrong_answer.yml). Include the question, the expected document and `fux ask --why "<question>"`. |
| A crash, an error or a broken command | [Open a bug report](https://github.com/arpitarya/fux/issues/new?template=bug_report.yml). Include `fux --version`, `fux doctor` and the command. |
| An idea: a format, a source, an agent integration | [Open a feature request](https://github.com/arpitarya/fux/issues/new?template=feature_request.yml). |
| A fix of your own | Open a pull request (see below). |
| A security issue | Don't open a public issue. See [SECURITY.md](SECURITY.md). |

> **Fix a wrong answer for yourself first.** `fux correct "<question>" <doc-that-answers-it>` records the words people ask with on the document that answers, durably. The issue still helps everyone else.

---

## Build and test

You need Python ≥ 3.12, [uv](https://docs.astral.sh/uv/) and Node ≥ 22.

```bash
git clone https://github.com/arpitarya/fux.git
cd fux
uv sync --extra dev
uv run pytest -q tests                         # fast unit suite
uv run pytest -q tests_e2e                     # the package as a user installs it
node --test node/test/*.test.mjs               # the Node reader's own units
```

Without uv, install all four packages at once:

```bash
pip install -e packages/fux-core -e packages/fux-reader -e packages/fux-writer -e ".[dev]"
```

- **Both Python suites are maintained**, and a feature isn't done until both cover it and pass.
- **Run both suites whole** before believing a change is done.
- **Two invocations fail for reasons that aren't failures**: the bare `node --test node/test`, and a hand-built test repo with no `.fux/config/pii.toml`. [`work/MACHINE.md`](work/MACHINE.md) has what to type instead.

---

## Rules every change follows

fux is governed by **standing records**: one Markdown file per decision, in [`records/`](records/README.md).

- **The records are the spec.** A change to an SR-owned component updates its owning record in the same commit, and CI checks it ([L0](records/0002_LAW-0-authority.md)). The owner is in the register's Ownership table. Install the guard once:

  ```bash
  ln -sf ../../scripts/sr-guard.sh .git/hooks/commit-msg
  ```

- **Deterministic.** Same index and query, same bytes out, on every machine ([L4](records/0006_LAW-4-deterministic.md)).
- **Offline by default.** Nothing on a default path touches the network ([L5](records/0007_LAW-5-offline-by-default.md)).
- **$0 and FOSS-only.** No paid or copyleft dependency, ever ([L2](records/0004_LAW-2-zero-cost.md)).
- **Ranking changes need evidence.** A change that moves ranking ships only through the standing bar, with a measured run ([L13](records/0015_LAW-13-the-standing-bar.md)). A pre-registered threshold never moves.
- **The benchmark's answer key is sealed.** Don't edit anything under `work/golden/` ([L11](records/0013_LAW-11-sealed-answer-key.md)).
- **Every relative link in a live document must resolve.** `tests/test_doc_links.py` checks it.

---

## Pull requests

1. **Keep it to one change.**
2. **Add tests** to the suite that covers the behaviour, and to both suites for a user-facing feature.
3. **Run** `uv run pytest -q tests`, `uv run pytest -q tests_e2e` and, if you touched `node/`, the Node tests.
4. **Update the owning record**, and add a line to [`CHANGELOG.md`](CHANGELOG.md) under *Unreleased* if users will notice.

**How work is planned** is in [`work/OPEN-WORK.md`](work/OPEN-WORK.md), and [`CLAUDE.md`](CLAUDE.md) is the full guide, for people and agents.

By contributing, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
