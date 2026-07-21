#!/usr/bin/env python
"""Distill + pack the bundled embedding model (dev-only; heavy deps allowed HERE).

Takes the pinned teacher (Model2Vec `minishlab/potion-base-8M`, MIT), quantizes
its static token-embedding matrix to int8 with per-vector scales, and packs a
single `model.bin` the stdlib runtime (`fux.embed`) can read — asserted ≤10 MB.
Also exports `tests/data/embed_reference.json`: tokenizer-parity samples and
matrix spot checks the runtime unit tests verify against.

Reproduce:
    uv venv /tmp/distill && uv pip install --python /tmp/distill/bin/python model2vec
    /tmp/distill/bin/python tools/distill/distill.py

See README.md here for the full recipe + license notes (ADR 0006).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from model2vec import StaticModel

TEACHER = "minishlab/potion-base-8M"
MAGIC = b"FUXEMB1\0"
MAX_BYTES = 10 * 1024 * 1024

REPO = Path(__file__).resolve().parents[2]

TOKEN_SAMPLES = [
    "Hello, composite index!",
    "Héllo — naïve API_v2 costs $3.50!",
    "The exporter batches telemetry every thirty seconds.",
    "rollbacks complete within two minutes",
    "café décisions über straße",
    "snake_case and CamelCase and kebab-case",
    "line\nbreaks\tand   extra   spaces",
    "emoji 🎯 survives?",
    "12345 3.14159 0xdeadbeef",
    "",
    "a",
    "supercalifragilisticexpialidocious antidisestablishmentarianism",
    "SQL SELECT * FROM trades WHERE symbol = 'AAPL'",
    "中文字符 mixed with english",
    "[CLS] literal special text [SEP]",
]

NEIGHBOR_TRIPLES = [
    # (anchor, closer, farther) — semantic sanity, verified again at runtime
    ("how fast can we revert a bad deployment", "rollbacks complete within two minutes", "lunch is served at noon"),
    ("database storage engine choice", "we chose sqlite for local embedded storage", "the cafeteria menu rotates weekly"),
    ("telemetry flush cadence", "batches are flushed every thirty seconds", "accented names are supported"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "src/fux/embed/data")
    parser.add_argument("--reference", type=Path, default=REPO / "tests/data/embed_reference.json")
    args = parser.parse_args()

    print(f"loading teacher {TEACHER} …")
    model = StaticModel.from_pretrained(TEACHER)
    emb = np.asarray(model.embedding, dtype=np.float32)
    vocab_size, dim = emb.shape
    tokenizer = model.tokenizer
    id_to_token = [""] * vocab_size
    for token, idx in tokenizer.get_vocab().items():
        id_to_token[idx] = token
    assert all(id_to_token), "vocab has holes"

    _license_check()

    # per-vector int8 quantization: scale = max|v| / 127 (zero rows → scale 1)
    maxabs = np.abs(emb).max(axis=1)
    scales = np.where(maxabs > 0, maxabs / 127.0, 1.0).astype(np.float32)
    quantized = np.clip(np.round(emb / scales[:, None]), -127, 127).astype(np.int8)

    args.out.mkdir(parents=True, exist_ok=True)
    bin_path = args.out / "model.bin"
    _pack(bin_path, id_to_token, scales, quantized)
    size = bin_path.stat().st_size
    sha = hashlib.sha256(bin_path.read_bytes()).hexdigest()
    assert size <= MAX_BYTES, f"bundle {size} bytes exceeds the 10 MB budget"
    print(f"packed {bin_path}  ({size / 1e6:.2f} MB, vocab {vocab_size}, dim {dim})")
    print(f"sha256 {sha}")

    meta = {
        "teacher": TEACHER,
        "license": "MIT",
        "vocab_size": vocab_size,
        "dim": dim,
        "quantization": "int8 per-vector symmetric, scale = max|v|/127",
        "sha256": sha,
        "size_bytes": size,
        "recipe": "tools/distill/distill.py (see tools/distill/README.md)",
    }
    (args.out / "model.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    reference = {
        "meta": {"vocab_size": vocab_size, "dim": dim, "sha256": sha},
        "token_samples": [
            {"text": text, "ids": tokenizer.encode(text, add_special_tokens=False).ids}
            for text in TOKEN_SAMPLES
        ],
        "vocab_spot": [
            {
                "id": int(i),
                "token": id_to_token[i],
                "scale": float(scales[i]),
                "first8": [int(x) for x in quantized[i, :8]],
            }
            for i in (0, 1, 100, 1000, vocab_size // 2, vocab_size - 1)
        ],
        "neighbor_triples": [
            {"anchor": a, "closer": b, "farther": c} for a, b, c in NEIGHBOR_TRIPLES
        ],
    }
    args.reference.parent.mkdir(parents=True, exist_ok=True)
    args.reference.write_text(
        json.dumps(reference, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.reference}")
    return 0


def _pack(path: Path, vocab: list[str], scales: np.ndarray, quantized: np.ndarray) -> None:
    vocab_size, dim = quantized.shape
    with path.open("wb") as fh:
        fh.write(MAGIC)
        fh.write(struct.pack("<III", 1, vocab_size, dim))
        for token in vocab:
            raw = token.encode("utf-8")
            fh.write(struct.pack("<H", len(raw)))
            fh.write(raw)
        fh.write(scales.astype("<f4").tobytes())
        fh.write(quantized.tobytes())


def _license_check() -> None:
    try:
        from huggingface_hub import hf_hub_download

        card = Path(hf_hub_download(TEACHER, "README.md")).read_text(encoding="utf-8")
        assert "license: mit" in card.lower(), "teacher model card is not MIT-licensed"
        print("license check: MIT ✓")
    except AssertionError:
        raise
    except Exception as exc:  # offline re-runs: the pin + ADR record the clearance
        print(f"license check skipped ({exc}); clearance recorded in ADR 0006", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
