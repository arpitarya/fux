/** The index write lock. Twin of `src/fux/maintain/lock.py` (SR-LOCKS, W-261).
 *
 * W-242 Tier 2 made Node a WRITER of the derived plane (`fux build`), so it must
 * exclude a Python `ingest` or `build` running on the same tree, and be excluded
 * by them, through the file alone ([SR-LOCKS](../../../records/0140_locks.md)):
 *
 * - `O_CREAT|O_EXCL` (`openSync(path, "wx")`) is the whole mechanism — one
 *   syscall, no read-then-write window;
 * - the body is `json.dump({"pid": N})` — Python's default separators, so a
 *   Python `holder()` parses a Node lock and the reverse;
 * - a lock that cannot be parsed reads as HELD (pid `-1`), never as absent;
 * - re-entry by the same pid is allowed, as `write_lock` allows it;
 * - **nothing here breaks a lock automatically.** A stale one is a person's call.
 *
 * A whole-file twin since W-261 moved the lock out of `runner.py`: the runner,
 * its status file and the cooperative stop are the daemon's, and Node runs no
 * daemon, so `runner.py` has no Node twin.
 */
import { closeSync, openSync, readFileSync, unlinkSync, writeSync } from "node:fs";
import { join } from "node:path";
import { FuxError } from "../errors.mjs";
import { fixed } from "../config/constants.mjs";
import { pyDumps } from "../compat/pyjson.mjs";
import { derivedDir } from "../store/cachedir.mjs";
import { fuxDir } from "../store/fuxdir.mjs";
import { RUNTIME_DIR } from "../derive/format.mjs";

export const LOCK_NAME = fixed("maintain", "write_lock");
const LOCK_MODE = fixed("maintain", "lock_mode");

export function lockPath(root) { return join(fuxDir(root), RUNTIME_DIR, LOCK_NAME); }

/** The pid recorded in the lock, `null` when none, `-1` when unparseable. */
export function holder(root) {
  let raw;
  try { raw = readFileSync(lockPath(root), "utf8"); } catch { return null; }
  // Unparseable is HELD, by nobody known: `-1`, as `holder()` answers.
  try {
    const pid = JSON.parse(raw).pid;
    return Number.isInteger(pid) ? pid : -1;
  } catch {
    return -1;
  }
}

/** Claim the lock atomically, or throw — a foreground writer never degrades. */
export function acquire(root) {
  const directory = derivedDir(root, RUNTIME_DIR);
  let fd;
  try {
    fd = openSync(join(directory, LOCK_NAME), "wx", LOCK_MODE);
  } catch (err) {
    if (err.code === "EEXIST") {
      throw new FuxError(
        `another fux process is writing this index (lock: ${lockPath(root)}). ` +
        "Wait for it, or - if you are certain no fux process is running - " +
        "delete that file and re-run",
      );
    }
    throw new FuxError(
      `cannot create the index write lock at ${lockPath(root)}: ${err.message}. ` +
      "Writing without it could corrupt the index if a second process starts",
    );
  }
  try {
    // `json.dump`'s default separators, so both runtimes write one shape.
    writeSync(fd, pyDumps({ pid: process.pid }, { sortKeys: false, ensureAscii: true }).replace(":", ": "));
  } finally {
    closeSync(fd);
  }
}

/** Drop the lock. Never throws — cleanup must not fail a finished write. */
export function release(root) {
  try { unlinkSync(lockPath(root)); } catch { /* already gone */ }
}

/** `write_lock` — hold it for `fn`, re-entering when this pid already holds it. */
export function withWriteLock(root, fn) {
  if (holder(root) === process.pid) return fn();
  acquire(root);
  try {
    return fn();
  } finally {
    release(root);
  }
}
