---
type: OpenItem
id: W-159
title: "W-159 — doctor's shadowing row cannot fire on Windows"
description: "_fux_on_path finds a shadowing `fux` with shutil.which, which resolves through PATHEXT — so it can never see the extensionless shim the test builds, and npm installs fux.cmd there. R1a mitigation 3 is Unix-only in practice; the test is skipped on Windows with its reason."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-159 — the shadowing row is Unix-only, and nothing said so

**Model: Sonnet.** The diagnosis is written; what is left is a PATHEXT-aware
lookup and a Windows-shaped test for it.

## What is true today

- **[SR-NODE-SEARCH](../../records/0153_node-search.md) R1a mitigation 3** is
  `fux doctor`'s row for *"a Node `fux` resolves before Python's"*.
- `doctor._fux_on_path()` calls `shutil.which("fux")`. On Windows that honours
  **PATHEXT**, so an extensionless `fux` is invisible — and
  `npm i -g fux-engine` writes **`fux.cmd`**, which `which` does find but whose
  first line is not a `#!/usr/bin/env node` shebang, so the shebang test that
  identifies the Node reader has nothing to read.
- **Net: the row cannot fire on Windows**, the platform where two globally
  installed `fux` binaries are most likely, and nothing in the record or the
  code said so.

## How it was found

`tests/test_doctor.py::test_a_node_fux_shadowing_python_is_reported` failed on
both Windows CI jobs — *"a node `fux` ahead of Python's was not reported"* —
because the shim it writes cannot be resolved there. It is **skipped on
Windows with that reason** as of 2026-09-13, rather than loosened into
something that passes.

## Definition of done

1. `_fux_on_path` identifies a Node `fux` on Windows: resolve through PATHEXT,
   and read a `.cmd`/`.ps1` shim's body for the `node` invocation npm writes
   rather than assuming a shebang.
2. A test that constructs the **Windows** shape (a `fux.cmd` calling node) and
   asserts the warn row, alongside the existing Unix one.
3. The skip in `tests/test_doctor.py` goes away in the same change.
4. SR-NODE-SEARCH says which platforms the mitigation covers — today it implies
   all of them.

## Out of scope

Making `fux` itself resolve differently, and anything about which binary
*should* win. The row reports; it does not arbitrate.
