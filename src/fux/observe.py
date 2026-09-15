"""`.fux/observers/` — the observe-only hook a consumer's analytics subscribes to.

**The third readable-source extension point**, beside
[`.fux/decoders/`](decode/__init__.py) and `.fux/fetchers/`, and the only one
that cannot change an answer. Ruled by Arpit on 2026-09-14 —
[SR-OBSERVE](../../records/0157_observe.md) — as a middleware fux exposes and a
consumer intercepts, narrowed to **observe-only** in the same conversation.

⚠ **No subscriber is named in this file, and that is a rule rather than a
style** (SR-OBSERVE decision 8): fux exposes the seam and knows nothing about
who uses it. The record carries the ruling's own wording, which does name one;
`tests/test_observe.py::test_fux_carries_no_knowledge_of_any_subscriber` greps
this package for it, and caught this docstring quoting the ruling verbatim.

## What a consumer gets, and what it can never reach

After a verb has fully rendered — stdout flushed, exit code fixed — fux calls
every `observe(record)` in `.fux/observers/*.py`, in sorted filename order,
with **one frozen record of counts**:

    verb · args_hash · band · answerable · n_results · n_related ·
    refer_verdicts{} · ms · expand_used · q_arms · fux_version

🔴 **The question is not in it. Nor is any expansion text, document id, path,
snippet or answer.** Every value is a count, a boolean, a name from a fixed
vocabulary, or a hash — and `test_observe.py` greps the emitted record for the
forbidden classes rather than trusting this paragraph. A field is added by
amending SR-OBSERVE decision 3, never by an observer asking for one.

## Why observe-only is structural here rather than a rule

An observer that could **return** something would make `ask` a function of
consumer code, and [L3](../../records/0005_LAW-3-deterministic.md) would be
gone — two machines with the same index would answer differently because one
had a file in a gitignored-looking directory. So:

- the dispatcher runs **after** every write the verb makes;
- it hands over a **copy**, not the live object;
- it has **no return path** — `observe`'s return value is discarded, and
  nothing reads it;
- and a **pre-verb hook is refused by design, not deferred.**

## Fail-open, and what that costs

An observer that raises is skipped for that run, with one `FUX_DEBUG` line
naming the file and the exception class. One that hangs is abandoned at
`[observe] max_ms`.

⚠ **`max_ms` abandons a thread; it does not kill one.** Python cannot safely
interrupt arbitrary consumer code, and a `SIGALRM` would land on whichever
thread the interpreter chose. So a slow observer stops **blocking** fux at the
cap and may keep running until the process exits — which is honest and is
stated in SR-OBSERVE rather than dressed up as a kill. What the cap guarantees
is the thing that matters: **a consumer's analytics cannot make `fux ask`
slow**, only itself.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["CONSUMER_DIR", "Record", "args_hash", "dispatch", "observers_in"]

#: Where a consumer's observers live. Committed, readable source by contract —
#: `.fux/runtime/` is the only derived directory under `.fux/`.
CONSUMER_DIR = ".fux/observers"

#: The one place a run records that an observer fired, for `fux doctor`'s
#: liveness row. **Gitignored, under `.fux/runtime/`** — it is a trace of use
#: and [L8](../../records/0010_LAW-8-use-record.md) keeps every one of those off
#: a committed byte.
LIVENESS_NAME = "observers.json"


@dataclass(frozen=True)
class Record:
    """One run, as counts. **The closed schema of SR-OBSERVE decision 3.**

    Frozen, and handed to each observer as a fresh `dict` so a subscriber that
    mutates what it is given cannot reach the next subscriber.
    """

    verb: str
    args_hash: str
    band: str | None
    answerable: bool | None
    n_results: int
    n_related: int
    refer_verdicts: dict = field(default_factory=dict)
    ms: int = 0
    expand_used: bool = False
    q_arms: int = 1
    fux_version: str = ""

    def as_dict(self) -> dict:
        return {
            "verb": self.verb,
            "args_hash": self.args_hash,
            "band": self.band,
            "answerable": self.answerable,
            "n_results": self.n_results,
            "n_related": self.n_related,
            "refer_verdicts": dict(self.refer_verdicts),
            "ms": self.ms,
            "expand_used": self.expand_used,
            "q_arms": self.q_arms,
            "fux_version": self.fux_version,
        }


#: What the verb that just ran wants reported. **A module-level dict, and the
#: shape is deliberate.**
#:
#: The dispatch point has to be *after* the verb has rendered, which means it
#: cannot be inside the verb — and the counts (`band`, `n_results`, the refer
#: verdicts) exist only inside it. Threading an out-parameter through every
#: handler's signature to reach a hook that must not influence them would put
#: the hook into the call graph of the thing it is forbidden to touch.
#:
#: ⚠ **One process, one verb.** fux's CLI runs a single command per process, so
#: there is no interleaving to protect against. `fux mcp` is the exception and
#: **does not dispatch at all** — a long-lived server calling consumer code per
#: request is a different decision with a different blast radius, and
#: SR-OBSERVE does not make it.
_PENDING: dict = {}


def note(**fields) -> None:
    """A verb reporting what it just did. **Never raises, returns nothing.**

    Called by the handler after it has rendered. Unknown keys are ignored
    rather than rejected: `Record`'s schema is closed by
    [SR-OBSERVE](../../records/0157_observe.md) decision 3 and by
    `_record_from`, and a handler passing something the schema does not carry
    should be a no-op here rather than an exception in a verb.
    """
    _PENDING.update(fields)


def _record_from(verb: str, argv: list[str], ms: int, version: str) -> Record:
    """Build the closed record from what the verb noted. Unknown keys drop."""
    noted = dict(_PENDING)
    return Record(
        verb=verb,
        args_hash=args_hash(argv),
        band=noted.get("band"),
        answerable=noted.get("answerable"),
        n_results=int(noted.get("n_results", 0)),
        n_related=int(noted.get("n_related", 0)),
        refer_verdicts=dict(noted.get("refer_verdicts", {})),
        ms=ms,
        expand_used=bool(noted.get("expand_used", False)),
        q_arms=int(noted.get("q_arms", 1)),
        fux_version=version,
    )


def args_hash(argv: list[str]) -> str:
    """SHA-256 over fux's **normalised** argv, truncated to 16 hex.

    **The contract shared with a subscriber's own transcript classifier**, so
    the two sides can join a fux run to the command that produced it without
    either side seeing the question.

    Normalisation, and every clause is load-bearing:

    - **The question is excluded.** Positional arguments are dropped entirely.
      A hash *of* the question is still a fingerprint of the question — two
      runs of the same query would match across consumers, which is the
      re-identification L8 exists to prevent.
    - **Flags are sorted**, so `--json --band` and `--band --json` are one
      command. A classifier joining on argv order would miss half its matches
      for no reason a user could see.
    - **Values are kept as given.** `--top 5` and `--top 05` are different
      commands, because the consumer typed different things and a join that
      silently merged them would over-count.
    - **The verb is kept and is first**, because it is the one positional that
      is not user content.

    ⚠ **A quoted or escaped command line normalises the same as a bare one.**
    By the time fux sees `argv`, the shell has already removed quoting — so
    `fux ask "a b"` and `fux ask a b` arrive as different argv and hash the
    same, since both drop their positionals. That is the behaviour the
    fixture on both sides pins.
    """
    verb = ""
    flags: list[str] = []
    i = 0
    # `argv` here is everything after the program name.
    if argv and not argv[0].startswith("-"):
        verb = argv[0]
        i = 1
    while i < len(argv):
        token = argv[i]
        if not token.startswith("-"):
            i += 1  # a positional: the question, or part of it. Dropped.
            continue
        if "=" in token:
            flags.append(token)
            i += 1
            continue
        # A flag whose next token is a value rather than another flag.
        if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
            # ⚠ Ambiguous by construction: `fux ask --band rollback` has a
            # value-less flag followed by the question. Treating the next token
            # as a value would fold question text into the hash, which is the
            # one thing this function may not do — so a bare flag NEVER
            # swallows the token after it, and a flag with a value is written
            # `--top=5` or is read as two tokens by argparse and as one flag
            # plus one dropped positional here.
            flags.append(token)
            i += 1
            continue
        flags.append(token)
        i += 1
    normalised = " ".join([verb, *sorted(flags)]).strip()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:16]


def observers_in(root: Path) -> list[Path]:
    """Every `*.py` in `.fux/observers/`, sorted by filename.

    Sorted because the order observers run in is part of the contract — an
    order that depended on the filesystem would make one machine's `FUX_DEBUG`
    output differ from another's for no stated reason.
    """
    directory = root / CONSUMER_DIR
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.py") if p.name != "__init__.py")


def dispatch(root: Path, record: Record, *, max_ms: int) -> None:
    """Hand `record` to every observer. **Never raises, never returns a value.**

    Called after the verb has rendered. The absence of a return value is the
    API: there is nothing for a caller to act on, so a future change that made
    an observer able to influence a verb would have to add one, visibly.

    ⚠ **`observers_in` is a `stat` on the common path** — a repo with no
    `.fux/observers/` pays one directory check per verb and nothing else, which
    is the same shape `_apply_pin` takes for an unpinned query.
    """
    try:
        paths = observers_in(root)
    except Exception:  # pragma: no cover - a hook must not fail a verb
        return
    if not paths:
        return

    # 🔴 **fux's stdout is taken away for the whole dispatch**, and the first
    # version of this function did not do it. An observer that calls `print`
    # appended to the answer — `ask --json` emitted valid JSON followed by the
    # observer's line, which is a consumer's code reaching stdout and exactly
    # what decision 5 forbids. Found by the byte-identity test, not reasoned
    # about: it is the one test in the suite written to be hostile.
    #
    # ⚠ **Swapped, not restored per observer, and the ordering is what makes
    # that safe.** `dispatch` is the last thing `cli.main` does before it
    # returns, so fux itself never prints again — while an observer ABANDONED
    # at the cap keeps running on its thread and would otherwise print into a
    # stream fux had handed back. The sink outliving the dispatch is correct.
    #
    # **stderr is deliberately left alone.** An observer's diagnostics are its
    # own business and reach no contract: `find` pipes stdout, `--json` is
    # stdout, and nothing fux promises is on stderr.
    sink = io.StringIO()
    real_stdout, sys.stdout = sys.stdout, sink
    try:
        fired: list[str] = []
        for path in paths:
            if _run_one(path, record, max_ms=max_ms):
                fired.append(path.name)
    finally:
        sys.stdout = real_stdout
    if sink.getvalue():
        _debug(
            f"{len(sink.getvalue().splitlines())} line(s) written to stdout by an "
            "observer were discarded - an observer may not reach the answer"
        )
    _record_liveness(root, [p.name for p in paths], fired)


def _run_one(path: Path, record: Record, *, max_ms: int) -> bool:
    """One observer, bounded and fail-open. `True` if it completed in time."""
    payload = record.as_dict()
    done = threading.Event()
    failure: list[BaseException] = []

    def call() -> None:
        try:
            module = _load(path)
            observe = getattr(module, "observe", None)
            if observe is None:
                raise AttributeError("no observe(record) function")
            # The return value is DISCARDED, deliberately and visibly.
            observe(payload)
        except BaseException as exc:  # noqa: BLE001 - fail-open is the contract
            failure.append(exc)
        finally:
            done.set()

    # `daemon=True` so a hung observer cannot keep the process alive after the
    # verb has answered. See the module docstring: the cap stops fux WAITING,
    # which is what a consumer's latency budget needs; it does not stop the
    # observer running, because Python cannot safely interrupt arbitrary code.
    thread = threading.Thread(target=call, name=f"fux-observe-{path.name}", daemon=True)
    thread.start()
    if not done.wait(timeout=max(max_ms, 0) / 1000.0):
        _debug(f"observer {path.name} exceeded [observe] max_ms={max_ms}; abandoned")
        return False
    if failure:
        _debug(f"observer {path.name} raised {type(failure[0]).__name__}; skipped")
        return False
    return True


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"fux_observer_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _debug(message: str) -> None:
    """One line on stderr, only under `FUX_DEBUG`.

    **Not a warning and not a `fux doctor` row on its own.** A consumer's
    broken analytics is the consumer's problem and must not make fux look
    broken to somebody who asked a question — `fux doctor`'s liveness row is
    where a persistently silent observer becomes visible.
    """
    if os.environ.get("FUX_DEBUG"):
        print(f"fux: {message}", file=sys.stderr)


def _record_liveness(root: Path, present: list[str], fired: list[str]) -> None:
    """Write which observers ran, for `fux doctor`. **Never raises.**

    🔴 **Gitignored, under `.fux/runtime/`.** It is a durable trace that
    somebody ran a query, which is exactly what
    [L8](../../records/0010_LAW-8-use-record.md) keeps off a committed byte —
    and *inside `.fux/`* is not the test, the gitignored path is.
    """
    import json

    try:
        from .derive import format as derive_fmt

        directory = derive_fmt.runtime_dir(root)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / LIVENESS_NAME).write_text(
            json.dumps({"present": sorted(present), "fired": sorted(fired)}, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:  # pragma: no cover - liveness must not fail a verb
        pass


def liveness(root: Path) -> dict:
    """What `fux doctor` reads back. `{}` when no run has been observed."""
    import json

    try:
        from .derive import format as derive_fmt

        path = derive_fmt.runtime_dir(root) / LIVENESS_NAME
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover
        return {}
