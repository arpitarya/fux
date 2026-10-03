"""The committed offset-table fixture, decoded by Python (W-242 step 8).

`idx-fixture.idx` holds three entries packed by `format.pack_entry`;
`idx-fixture.json` holds the rows they decode to. `node/test/accel.test.mjs`
decodes the same two files with `derive/format.mjs`. **One file, two readers**:
a transposed field in either decoder is a silent miss at query time, never an
error, so the only place it can be caught is here. The rows carry an offset past
2^32 and the u16/u32 maxima so a narrowed field fails too.
"""

from __future__ import annotations

import json
from pathlib import Path

from fux.derive import format as fmt

HERE = Path(__file__).parent


def test_the_fixture_decodes_to_its_rows():
    buf = (HERE / "idx-fixture.idx").read_bytes()
    expected = json.loads((HERE / "idx-fixture.json").read_text(encoding="utf-8"))
    assert expected["entry_size"] == fmt.ENTRY_SIZE
    assert len(buf) == fmt.ENTRY_SIZE * len(expected["rows"])
    for i, row in enumerate(expected["rows"]):
        term, *rest = fmt.unpack_entry(buf, i)
        decoded = [term.hex(), *[list(v) if isinstance(v, tuple) else v for v in rest]]
        assert decoded == row, f"entry {i}"


def test_packing_the_rows_reproduces_the_file():
    expected = json.loads((HERE / "idx-fixture.json").read_text(encoding="utf-8"))
    packed = b"".join(
        fmt.pack_entry(bytes.fromhex(r[0]), r[1], r[2], r[3], tuple(r[4]), tuple(r[5]), r[6], r[7], r[8])
        for r in expected["rows"]
    )
    assert packed == (HERE / "idx-fixture.idx").read_bytes()
