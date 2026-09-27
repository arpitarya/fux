"""Every declared shape fux has, as package data — one directory, five files.

Loaded only through [`fux.schema.load`](../schema.py), which takes the package
name from `src/fux/constants.toml` `[schema_files] package`. Nothing here is
imported for its code; the module exists so `importlib.resources` resolves the
directory in a wheel and in an editable install alike.

**Each file keeps the owner of the shape it declares**, by an explicit
file-level row in `records/README.md` §OWNERSHIP — this directory's own row
(SR-LAWS) catches only a file added without one, and a test refuses that.
[SR-LAWS](../../../records/0001_LAWS.md) decision 6.
"""
