"""One schema mechanism, used by every plane that has a declared shape.

A **schema** here is a JSON file that sits beside the code that reads or writes
a shape, declares that shape's fields, and carries a worked example. It is
**not** a template: nothing copies it. It is loaded, and the code is checked
against it.

## Why this is one module and not five

Five planes have declared shapes — the committed record, the derived runtime,
the graph plane, the local runtime state, and the `--json` output every agent
parses. Writing five small validators would have produced five subtly different
ideas of what "required" means, which is the drift this whole exercise exists
to stop. **One mechanism, five declarations.**

## Where a schema file lives, and why it is not negotiable

**Beside the code that owns the shape** — `store/index-record.schema.json`,
`derive/runtime.schema.json`, and so on. Never in a shared `schemas/` directory.

The reason is ownership, not tidiness. This repo assigns every component to
exactly one decision record **by directory**, so a shared directory would have
one record owning shapes that belong to five. That is not hypothetical: the
first version of the record schema was written into `src/fux/templates/`, and
the ADR guard refused the commit because `templates/` belongs to ADR-FETCHER —
a record with nothing to say about the record shape. **Beside the code, the
ownership is correct by construction.**

## What a declaration looks like

```json
{
  "schema": "fux.index.v2",
  "fields": {
    "id":  {"type": "str", "required": "always"},
    "ver": {"type": "int", "required": "always", "default": 0},
    "src": {"type": "str", "required": "always", "enum": ["git", "url"]}
  },
  "example": {"id": "file:a.md", "ver": 0, "src": "git"}
}
```

Supported per field: `type` (`str` `int` `bool` `list` `dict` `any`),
`required` (`always` · `never`, plus caller-defined conditions), `default`,
`enum`, `of` (element type for a list), `len`, `omit_when`, and any number of
documentation keys, which are ignored.

## Two rules that are the point of the whole mechanism

**A key the schema does not declare is refused**, wherever a builder is used.
An undeclared key used to reach disk and never be read again — no error, no
test, a field that exists forever and means nothing.

**`coerce` is for reading, `validate` is for writing.** A file fux reads back
may have been truncated, hand-edited or written by an older version, and a
*reporting* plane must degrade rather than raise; `coerce` returns only what is
declared and well-typed. A shape fux is about to *write* should be right, so
`validate` raises and names the field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

from .errors import FuxError

__all__ = ["Field", "Schema", "load", "TYPES"]

#: `any` is deliberately available and deliberately rare: it means *this shape
#: is genuinely heterogeneous*, not *nobody looked*. Every use of it in a
#: shipped schema carries a comment saying which.
TYPES: dict[str, type | tuple[type, ...]] = {
    "str": str,
    "int": int,
    "bool": bool,
    "list": list,
    "dict": dict,
    "any": object,
}


@dataclass(frozen=True)
class Field:
    name: str
    type: str = "any"
    required: str = "never"
    default: object = None
    enum: tuple | None = None
    of: str | None = None
    length: int | None = None
    has_omit: bool = False
    omit_when: object = None
    spec: dict = None  # the raw declaration, for callers reading extra keys

    @classmethod
    def parse(cls, name: str, spec: dict) -> "Field":
        return cls(
            name=name,
            type=spec.get("type", "any"),
            required=spec.get("required", "never"),
            default=spec.get("default"),
            enum=tuple(spec["enum"]) if "enum" in spec else None,
            of=spec.get("of"),
            length=spec.get("len"),
            has_omit="omit_when" in spec,
            omit_when=spec.get("omit_when"),
            spec=spec,
        )

    def type_ok(self, value) -> bool:
        expected = TYPES.get(self.type, object)
        if self.type == "any":
            return True
        # `bool` is an `int` subclass, so a naive isinstance lets `True` through
        # an `int` field and writes `true` where a number belongs.
        if isinstance(value, bool) is not (self.type == "bool"):
            return False
        return isinstance(value, expected)


class Schema:
    """One declared shape. Immutable; loaded once and cached."""

    def __init__(self, raw: dict, *, origin: str) -> None:
        self.raw = raw
        self.origin = origin
        self.id = raw.get("schema")
        declared = raw.get("fields") or {}
        #: ⚠ **`fields` may be a LIST, and that is not sloppiness.** A binary
        #: layout is ORDERED — the offset table's 62-byte entry is a sequence of
        #: struct codes, and its order *is* the format. Forcing it into a
        #: name->spec mapping would either lose the order or lie about it being
        #: unimportant, which is exactly the kind of documentation that reads as
        #: authority and is wrong. A positional shape declares `positional`
        #: instead of `fields`, and is validated by its own test rather than by
        #: the generic object path.
        self.positional: list = declared if isinstance(declared, list) else []
        self.fields: dict[str, Field] = (
            {name: Field.parse(name, spec) for name, spec in declared.items()}
            if isinstance(declared, dict)
            else {}
        )

    # -- reading -------------------------------------------------------------

    def coerce(self, raw) -> dict:
        """Keep only declared, well-typed fields. **Never raises.**

        For reading a file back. A truncated, hand-edited or older-version file
        degrades to "what of it we can still believe" rather than taking down a
        reporting path. Anything undeclared or mistyped is dropped silently,
        because there is no caller who could act on the complaint.
        """
        if not isinstance(raw, dict):
            return {}
        out: dict = {}
        for name, field in self.fields.items():
            if name not in raw:
                continue
            value = raw[name]
            if not field.type_ok(value):
                continue
            if field.enum is not None and value not in field.enum:
                continue
            if field.of is not None and isinstance(value, list):
                element = TYPES.get(field.of, object)
                if not all(isinstance(v, element) and not isinstance(v, bool) for v in value):
                    continue
            out[name] = value
        return out

    # -- writing -------------------------------------------------------------

    def build(self, values: dict, *, conditions=None) -> dict:
        """Assemble a shape: defaults applied, `omit_when` values dropped, and
        **an undeclared key refused**."""
        unknown = sorted(k for k in values if k not in self.fields)
        if unknown:
            raise FuxError(
                f"{self.origin}: field(s) not declared: {', '.join(unknown)}. "
                "Add them to the schema — with a type — or fix the spelling"
            )
        out: dict = {}
        for name, field in self.fields.items():
            if name in values:
                value = values[name]
            elif field.default is not None and field.required == "always":
                value = field.default
            else:
                continue
            if field.has_omit and value == field.omit_when:
                continue
            out[name] = value
        return out

    def validate(self, obj: dict, *, label: str = "", conditions=None) -> None:
        """Check a shape against its declaration. Raises on the first fault.

        `conditions` maps a `required` value other than `always`/`never` to a
        callable taking the object and returning whether it applies — which is
        how a shape says *required only for a non-git record* without this
        module knowing what a git record is.
        """
        where = f"{label or self.origin}"
        if not isinstance(obj, dict):
            raise FuxError(f"{where}: expected an object, got {type(obj).__name__}")

        unknown = sorted(k for k in obj if k not in self.fields and not k.startswith("_"))
        if unknown:
            raise FuxError(f"{where}: undeclared field(s): {', '.join(unknown)}")

        conditions = conditions or {}
        for name, field in self.fields.items():
            if name not in obj:
                if field.required == "always":
                    raise FuxError(f"{where}: missing required field {name!r}")
                test = conditions.get(field.required)
                if test is not None and test(obj):
                    raise FuxError(
                        f"{where}: {name!r} is required when {field.required!r} holds"
                    )
                continue

            value = obj[name]
            if not field.type_ok(value):
                raise FuxError(
                    f"{where}: {name!r} must be {field.type}, got {type(value).__name__}"
                )
            if field.enum is not None and value not in field.enum:
                raise FuxError(
                    f"{where}: {name!r} must be one of {list(field.enum)}, got {value!r}"
                )
            if field.of is not None and isinstance(value, list):
                element = TYPES.get(field.of, object)
                bad = [v for v in value if not isinstance(v, element) or isinstance(v, bool)]
                if bad:
                    raise FuxError(f"{where}: every element of {name!r} must be {field.of}")
            if field.length is not None and len(value) != field.length:
                raise FuxError(
                    f"{where}: {name!r} must have length {field.length}, got {len(value)}"
                )
            if field.has_omit and value == field.omit_when:
                raise FuxError(
                    f"{where}: {name!r} == {field.omit_when!r} must be OMITTED, not written"
                )

    def shape(self, name: str) -> "Schema":
        """One nested shape out of a multi-shape file.

        Several schemas declare a family rather than a single object — the
        derived plane's four, this package's local state, the output contract's
        four payloads. They live in one file because they are written by one
        module and versioned by **one string**; splitting them would invite
        three to be updated and the fourth forgotten.
        """
        try:
            return Schema(self.raw[name], origin=f"{self.origin}#{name}")
        except KeyError:
            raise FuxError(f"{self.origin}: declares no shape named {name!r}") from None

    # -- examples ------------------------------------------------------------

    def examples(self) -> dict:
        """`{name: example}` for every example this schema carries.

        Both `example` (one) and `examples` (a named map) are supported, because
        a shape with two genuinely different forms — a git record and a hashed
        url record — is badly served by being made to pick one.
        """
        found: dict = {}
        if "example" in self.raw:
            found["example"] = self.raw["example"]
        for name, value in (self.raw.get("examples") or {}).items():
            found[name] = value
        return found


@lru_cache(maxsize=None)
def load(package: str, name: str) -> Schema:
    """Load a schema shipped as package data. Cached — schemas cannot change
    under a running process.

    A missing or malformed schema is a **broken installation**, not a user
    error, and says so. The alternative is a default shape silently taking over
    and reading or writing something nobody declared.
    """
    try:
        raw = json.loads((resources.files(package) / name).read_text("utf-8"))
    except (OSError, ValueError, ModuleNotFoundError) as exc:
        raise FuxError(
            f"schema {package}/{name} is missing or unreadable ({exc}). "
            "This is a broken install, not a configuration problem — reinstall fux-engine"
        ) from exc
    return Schema(raw, origin=name)
