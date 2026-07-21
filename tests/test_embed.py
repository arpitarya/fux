"""fux.embed runtime vs the distill-exported reference (tokenizer parity etc.)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from fux.embed.model import DATA_PATH, MAX_TOKENS, Model, get_model

REFERENCE = Path(__file__).parent / "data" / "embed_reference.json"

pytestmark = pytest.mark.skipif(
    not DATA_PATH.is_file(), reason="model bundle not built (tools/distill)"
)


@pytest.fixture(scope="module")
def model() -> Model:
    return Model()


@pytest.fixture(scope="module")
def reference() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def test_bundle_pinned_by_sha(reference):
    sha = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    assert sha == reference["meta"]["sha256"]
    assert DATA_PATH.stat().st_size <= 10 * 1024 * 1024  # the hard budget


def test_header_matches_reference(model, reference):
    assert model.vocab_size == reference["meta"]["vocab_size"]
    assert model.dim == reference["meta"]["dim"]


def test_vocab_and_matrix_spot_checks(model, reference):
    for spot in reference["vocab_spot"]:
        i = spot["id"]
        assert model.vocab[i] == spot["token"]
        assert model.scales[i] == pytest.approx(spot["scale"], rel=1e-6)
        assert list(model.row(i)[:8]) == spot["first8"]


def test_tokenizer_parity_with_teacher(model, reference):
    for sample in reference["token_samples"]:
        assert model.tokenize(sample["text"]) == sample["ids"], sample["text"]


def test_embed_deterministic(model):
    a = model.embed("rollbacks complete within two minutes")
    b = model.embed("rollbacks complete within two minutes")
    assert a == b
    assert a is not None and len(a.q) == model.dim


def test_all_oov_and_empty_return_none(model):
    assert model.embed("") is None
    assert model.embed("🎯 🎯 🎯") is None  # every token is [UNK]


def test_neighbor_triples_semantic_sanity(model, reference):
    for triple in reference["neighbor_triples"]:
        anchor = model.embed(triple["anchor"])
        closer = model.embed(triple["closer"])
        farther = model.embed(triple["farther"])
        assert Model.similarity(anchor, closer) > Model.similarity(anchor, farther), triple


def test_long_input_truncates(model):
    long_text = "word " * (MAX_TOKENS * 2)
    vec = model.embed(long_text)
    assert vec is not None  # no blow-up; policy recorded in ADR 0006


def test_get_model_singleton():
    assert get_model() is get_model()


def test_embed_package_is_stdlib_only():
    src = Path(__file__).parent.parent / "src" / "fux" / "embed"
    allowed_local = ("fux.", ".errors", ".model", ".store")
    for path in src.rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                module = stripped.split()[1]
                assert not module.startswith(("numpy", "torch", "model2vec")), (path, line)
