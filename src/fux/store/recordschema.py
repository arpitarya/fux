"""The committed record's shape, loaded from one schema instead of four places.

`store/index-record.schema.json` declares every field of a committed record: its
type, when it is required, its default, whether it carries display text, whether
a delta ingest may carry it forward, and whether it is omitted rather than
written false.

## What this replaces, and why it was worth replacing

The shape existed in four places and agreed with itself only by habit:

| where | what it knew |
|---|---|
| `ingest/run.py` | assembled the dict — **twice**, once for `git` and once for `url` |
| `ingest/run.py` | `EXTRACTED_FIELDS` — which fields a delta ingest may carry |
| `store/writer.py` | `DISPLAY_FIELDS` — which fields L5 forbids on a hashed record |
| ADR-RECORD | the prose description everyone reads |

**Nothing compared them.** Adding a display field meant remembering to touch a
tuple in a different module, and forgetting was silent: the field would ship,
and L5's check simply would not look at it. That is the same shape as the
governance gap W-82 §5.3 records — a rule that is real, and a check that is
narrower than it reads.

## What this deliberately does NOT do

**It does not change a single committed byte, and a test asserts that.**
`canonical_dumps` sorts keys, so the order in the schema is presentation and
cannot reach the index. The field set, the defaults and `omit_when` *can*, which
is why `schema` in the schema must equal `format.SCHEMA_ID` — two fux versions
with different shapes must never both call their output `fux.index.v2`.

**It is not a validator that runs on every write.** `write_index` already
enforces the one rule that closes a leak (L5's meta policy) and
`canonical_dumps` already refuses floats, nulls and hostile text. Adding a
third gate on the hot path would cost time to re-check what those two already
guarantee. `validate()` here is for tests and for callers building records by
hand — it is a tool, not a checkpoint.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from ..errors import FuxError

__all__ = [
    "Field",
    "RecordShape",
    "shape",
    "build",
    "display_fields",
    "carried_fields",
    "validate",
]

#: Beside the code that owns it, NOT under `templates/`, and the reason is
#: ownership rather than tidiness: `src/fux/templates/` is claimed by
#: ADR-FETCHER (the fetcher files live there), so a record-shape template in it
#: would be owned by a record with nothing to say about the record shape.
#: `src/fux/store/` is ADR-INDEX-LIFECYCLE's, which is exactly right -- so the
#: ownership is correct BY CONSTRUCTION instead of by a carve-out somebody has
#: to remember. The ADR guard caught this on the first commit attempt.
SCHEMA_NAME = "index-record.schema.json"

_PY_TYPES = {"str": str, "int": int, "bool": bool, "list": list, "dict": dict}


class Field:
    """One declared field. Frozen by convention — nothing here mutates it."""

    __slots__ = (
        "name", "type", "required", "default", "enum",
        "display", "carried", "has_omit", "omit_when",
    )

    def __init__(self, name: str, spec: dict) -> None:
        self.name = name
        self.type = spec["type"]
        self.required = spec.get("required", "never")
        self.default = spec.get("default")
        self.enum = tuple(spec["enum"]) if "enum" in spec else None
        self.display = bool(spec.get("display", False))
        self.carried = bool(spec.get("carried", False))
        #: Sentinel-free on purpose: `omit_when` is only ever `false` today, and
        #: a `has_omit` flag beats a magic value that could collide with a
        #: legitimate one.
        self.has_omit = "omit_when" in spec
        self.omit_when = spec.get("omit_when")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Field({self.name!r}, {self.type!r}, required={self.required!r})"


class RecordShape:
    def __init__(self, raw: dict) -> None:
        self.schema: str = raw["schema"]
        self.fields: dict[str, Field] = {
            name: Field(name, spec) for name, spec in raw["fields"].items()
        }

    def __contains__(self, name: str) -> bool:
        return name in self.fields

    @property
    def display(self) -> tuple[str, ...]:
        return tuple(n for n, f in self.fields.items() if f.display)

    @property
    def carried(self) -> tuple[str, ...]:
        return tuple(n for n, f in self.fields.items() if f.carried)


@lru_cache(maxsize=1)
def shape() -> RecordShape:
    """The parsed schema. Cached — it is package data and cannot change under us.

    A missing or malformed template is a **broken installation**, not a user
    error, and says so: the alternative is a default shape silently taking over
    and writing an index nobody declared.
    """
    try:
        raw = json.loads((resources.files("fux.store") / SCHEMA_NAME).read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise FuxError(
            f"the index-record schema is missing or unreadable ({exc}). "
            "This is a broken install, not a configuration problem — reinstall fux-engine"
        ) from exc
    return RecordShape(raw)


def display_fields() -> tuple[str, ...]:
    """Fields carrying text a human can read. L5 forbids these on a hashed record."""
    return shape().display


def carried_fields() -> tuple[str, ...]:
    """Fields a delta ingest may reuse from the prior record.

    ⚠ `edges` is **not** among them, and that is the interesting exclusion: it
    is the one field the rest of the corpus can change without this document
    changing, so carrying it forward would freeze a link that a newly added
    document should have resolved.
    """
    return shape().carried


def build(**values) -> dict:
    """Assemble one record: apply defaults, drop `omit_when` values, refuse
    anything the schema does not declare.

    **The last clause is the point.** A typo'd key used to sail through into the
    committed index and simply never be read again — no error, no test, a field
    that exists forever and means nothing.
    """
    shp = shape()
    unknown = [k for k in values if k not in shp.fields]
    if unknown:
        raise FuxError(
            f"record field(s) not declared in {SCHEMA_NAME}: {', '.join(sorted(unknown))}. "
            "Add the field to the schema — with its type and whether it is display text — "
            "or fix the spelling"
        )

    record: dict = {}
    for name, field in shp.fields.items():
        if name in values:
            value = values[name]
        elif field.default is not None and field.required == "always":
            value = field.default
        else:
            continue
        if field.has_omit and value == field.omit_when:
            continue  # absent, not false — a live record's shape is unchanged
        record[name] = value
    return record


def validate(record: dict) -> None:
    """Check one record against the schema. Raises `FuxError` on the first fault.

    For tests and for callers assembling records by hand. **Not called on the
    write path** — see the module docstring for why that is deliberate.
    """
    shp = shape()
    doc_id = record.get("id", "<no id>")

    unknown = [k for k in record if k not in shp.fields]
    if unknown:
        raise FuxError(f"{doc_id}: undeclared field(s): {', '.join(sorted(unknown))}")

    for name, field in shp.fields.items():
        if name not in record:
            if field.required == "always":
                raise FuxError(f"{doc_id}: missing required field {name!r}")
            if field.required == "non-git" and record.get("src") not in (None, "git"):
                raise FuxError(
                    f"{doc_id}: {name!r} is required for a non-git record. A missing value means "
                    "something bypassed the resolution layer, and guessing is the failure L5 prevents"
                )
            if field.required == "when-hashed" and record.get("meta") == "hashed":
                raise FuxError(f"{doc_id}: {name!r} is required when meta is 'hashed'")
            continue

        value = record[name]
        expected = _PY_TYPES[field.type]
        # bool is an int subclass; an `int` field must not silently accept True.
        if isinstance(value, bool) is not (field.type == "bool") or not isinstance(value, expected):
            raise FuxError(
                f"{doc_id}: {name!r} must be {field.type}, got {type(value).__name__}"
            )
        if field.enum is not None and value not in field.enum:
            raise FuxError(
                f"{doc_id}: {name!r} must be one of {list(field.enum)}, got {value!r}"
            )
        if field.has_omit and value == field.omit_when:
            raise FuxError(
                f"{doc_id}: {name!r} == {field.omit_when!r} must be OMITTED, not written. "
                "Absent-when-false keeps a live record's shape unchanged (ADR-ARCHIVED-CONTENT)"
            )
