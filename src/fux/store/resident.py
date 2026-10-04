"""The loaded index, held across calls by a process that stays up (W-249).

**[SR-MCP](../../../records/0136_mcp.md) decision 13.** `fux mcp` and `fux serve`
answer many calls from one process, and until this module each call re-read the
committed shards from disk and re-parsed them — on this repository ~330 ms of a
~430 ms `fux_search`, the interpreter start-up that MCP exists to avoid paid
again in JSON. One `Holder` per process now keeps **the loaded index**: each
shard's record lines as `reader.raw_record_lines` returns them, and the parsed
records `reader.read_index` builds from them. Nothing else.

🔴 **This is residency of the INPUT, never a memo of an OUTPUT.** No ranked list,
payload, band or passage is kept; every call still ranks, composes and renders
from scratch over the held records. A query-result cache is W-242's T3, refused
in [`work/compare/shared-runtime.compare.md`](../../../work/compare/shared-runtime.compare.md),
and this module does not reopen it — the same question asked twice is answered
twice.

## The key

`(digest of .fux/runtime/stamp.json, every committed shard's name, size and
mtime_ns)`, recomputed **before every call**. The stamp alone is NOT enough, and
the reason is the order of writes: `fux ingest --no-accelerator`, a `git pull`,
a checkout or a merge rewrites `.fux/index/` and leaves the stamp alone until
the next `fux build`, so a stamp-only key would serve the previous index while
the per-call path, which re-reads the shards, served the new one. The shard
stats are what `derive/accel.py::is_fresh` already compares the stamp against,
so the key is the per-call path's own staleness signal plus the stamp.

- **An absent `.fux/runtime/` is a key, not an error**: the digest half is
  `None`, re-read before every call like a present one, and the shards are
  still held — a fresh clone that never ran `fux build` takes the scan path
  exactly as before and still reads its shards once.
- **A stamp rewritten with identical bytes does not reload.** `fux build` over
  unchanged shards writes the same stamp, and every file it derives is
  byte-identical (L4), so there is nothing new to load.
- **A call that read anything from disk re-computes the key when it ends**, and
  if the index moved under it the state is dropped rather than kept. Shards
  are replaced by rename (`writer._atomic_write`), so each file read is whole;
  the second key is what proves the SET was one index state. A call that read
  nothing new — the steady state — pays one key computation: one stamp read and
  a `stat` per shard.

⚠ **Size and mtime are a filter, not proof** — [SR-RUNTIME-STAMP](../../../records/0124_runtime-stamp.md)
decision 3's caveat, inherited: a shard rewritten to the same size with its
mtime restored by hand would not be seen. The accelerator's freshness check has
the same exposure and the same answer.

## What is NOT held, deliberately

- **The derived plane** — the accelerator's doc table and postings, `graph.json`,
  `mined.json`. `fux build` rewrites them IN PLACE, not by rename, and over
  unchanged shards it leaves the stamp byte-identical — so a handle filled
  lazily across calls could keep a read taken mid-rewrite for the life of the
  process, with no key change to evict it. Per call they cost what they always
  did: the postings blocks of the query's own terms, and one small file each.
- **Committed configuration** — `fux.toml`, `tune.toml`, `output.toml`,
  `pii.toml`, `identifiers.toml`, the corrections file. They change without
  either half of the key moving, and each is already read per call (or, for
  `[mcp]`, once at start-up by SR-OUTPUT decision 17), so they stay that way.

## How a call reaches it

A holder does nothing until a call is bracketed by `Holder.call()`, which binds
this index state to a context variable for the duration of the call. The two
reader functions consult it and fall through to disk when nothing is bound, or
when what is bound is a different repository. So residency exists only inside
a bracketed call of a process that asked for it: a CLI verb, a test, or one of
`fux serve`'s own background jobs reads from disk exactly as before.
`fux serve` runs one thread per request, and a context variable is per thread,
so concurrent requests each see their own binding; a state's fills take its lock.

**The records are shared between calls, so they are read-only.** `read_index`
hands each caller a new outer dict (cheap), but the record dicts inside are the
held ones. Every caller reachable from the two servers only reads them.
"""

from __future__ import annotations

import contextlib
import contextvars
import threading
from pathlib import Path

from .format import content_sha, index_dir

__all__ = ["Holder", "held_lines", "held_records", "state_key"]


def state_key(root: Path) -> tuple:
    """`(stamp digest or None, ((shard name, size, mtime_ns), ...))`.

    Raises `OSError` when a shard vanishes between the listing and its `stat`
    — an index mid-rewrite, which `Holder.call` answers by holding nothing for
    that call.
    """
    from ..derive import format as derive_fmt
    from .reader import iter_shard_paths

    try:
        stamp = (derive_fmt.runtime_dir(root) / derive_fmt.STAMP_NAME).read_bytes()
    except FileNotFoundError:
        digest = None
    else:
        digest = content_sha(stamp)
    shards = []
    for path in iter_shard_paths(root):
        st = path.stat()
        shards.append((path.name, st.st_size, st.st_mtime_ns))
    return digest, tuple(shards)


class _State:
    """One index state: its key, and whatever calls have read of it so far."""

    def __init__(self, root: Path, key: tuple) -> None:
        self.key = key
        self.dir = index_dir(root)
        self.dir_resolved = self.dir.resolve()
        self.lock = threading.Lock()
        self.lines: dict[str, tuple[dict, list[bytes]]] = {}
        self.records: dict[str, dict] | None = None
        #: Disk reads made filling this state. A test's spy; the servers ignore it.
        self.reads = 0

    def covers(self, directory: Path) -> bool:
        return directory == self.dir or directory == self.dir_resolved


class _Binding:
    """What `Holder.call` binds: the state, and whether this call filled it."""

    def __init__(self, state: _State) -> None:
        self.state = state
        self.filled = False


_BOUND: contextvars.ContextVar[_Binding | None] = contextvars.ContextVar(__name__, default=None)


def held_lines(path: Path, read) -> tuple[dict, list[bytes]] | None:
    """`raw_record_lines(path)` from the bound state, or `None` when unbound.

    `read` is the disk reader, called once per shard per index state. The
    header is copied and the lines list is a fresh list over the held bytes,
    so a caller that edits either cannot reach the next call.
    """
    binding = _BOUND.get()
    if binding is None or not binding.state.covers(path.parent):
        return None
    state = binding.state
    with state.lock:
        entry = state.lines.get(path.name)
        if entry is None:
            entry = read(path)
            state.lines[path.name] = entry
            state.reads += 1
            binding.filled = True
    header, lines = entry
    return dict(header), list(lines)


def held_records(root: Path, read) -> dict[str, dict] | None:
    """`read_index(root)` from the bound state, or `None` when unbound.

    `read` builds the records from the shards — through `held_lines`, so a
    state that already holds the lines parses them without reading a file.
    """
    binding = _BOUND.get()
    if binding is None or not binding.state.covers(index_dir(root)):
        return None
    state = binding.state
    with state.lock:
        records = state.records
    if records is None:
        # Outside the state's lock: `read` takes it once per shard.
        records = read(root)
        with state.lock:
            if state.records is None:
                state.records = records
                binding.filled = True
            records = state.records
    return dict(records)


class Holder:
    """The loaded index of ONE repository, kept for the life of a process.

    `root` is a path, or a callable returning one — `fux serve` finds its root
    on first use, not at start-up.
    """

    def __init__(self, root) -> None:
        self._root = root
        self._lock = threading.Lock()
        self._state: _State | None = None
        #: Index states this holder has started — one per distinct key. The
        #: count a test asserts on; it does not move when a call is served from
        #: what is already held.
        self.loads = 0

    def root(self) -> Path:
        return self._root() if callable(self._root) else self._root

    @property
    def state(self) -> _State | None:
        return self._state

    @contextlib.contextmanager
    def call(self):
        """Bracket one tool call or one request: key before, bind, re-key if filled."""
        root = self.root()
        try:
            key = state_key(root)
        except OSError:
            yield None  # the index is being rewritten: this call reads disk, as before
            return
        with self._lock:
            state = self._state
            if state is None or state.key != key:
                state = _State(root, key)
                self._state = state
                self.loads += 1
        binding = _Binding(state)
        token = _BOUND.set(binding)
        try:
            yield state
        finally:
            _BOUND.reset(token)
            if binding.filled:
                try:
                    moved = state_key(root) != key
                except OSError:
                    moved = True
                if moved:
                    with self._lock:
                        if self._state is state:
                            self._state = None
