/** The single, flat error type for the Node reader. Twin of `src/fux/errors.py`.
 *
 * Deliberately one class — no subclass hierarchy (CLAUDE.md, error contract).
 * Throw `FuxError` for expected, user-facing failures; internals keep throwing
 * and only the boundary (`fux.mjs`'s `main`) renders.
 */

export class FuxError extends Error {
  /** `exitCode` mirrors Python's: `0` ok · `1` error · `2` blocking · `130` interrupted. */
  constructor(message, { exitCode = 1 } = {}) {
    super(message);
    this.name = "FuxError";
    this.exitCode = exitCode;
  }
}
