"""FuxVec: sign quantization + the full-corpus Hamming scan (pure math).

Ported from archive/v0.26/tests/test_fuxvec.py's quantization/hamming/
doc_code/prefilter sections only. The archived file's integration tests
(the ADR-0006 zero-lexical-overlap "rescue", hybrid `find`/`ask --json`)
depend on the dense query lane, which M1 does not build — `code` is written
now, used at M2/M3 (handoff §3 scope fence). Not ported here; re-land with
the dense lane.
"""

from __future__ import annotations

from math import sqrt

from fux.embed.fuxvec import CODE_BYTES, doc_code, hamming, prefilter, quantize
from fux.embed.model import Vec


def vec(components) -> Vec:
    q = tuple(components)
    return Vec(q=q, scale=1.0, norm=sqrt(sum(x * x for x in q)) or 1.0)


def dims(n=256, fill=0):
    return [fill] * n


# -- quantization ------------------------------------------------------------


def test_code_is_32_bytes():
    assert len(quantize(vec(dims()))) == CODE_BYTES


def test_bit_is_set_for_positive_components():
    components = dims()
    components[0] = 5
    components[7] = 1
    components[8] = -3  # negative and zero must stay clear
    code = quantize(vec(components))
    bits = int.from_bytes(code, "little")
    assert bits >> 0 & 1 and bits >> 7 & 1
    assert not bits >> 8 & 1


def test_quantization_is_deterministic():
    components = dims()
    components[3] = 2
    assert quantize(vec(components)) == quantize(vec(components))


def test_hamming_counts_differing_bits():
    a, b = dims(), dims()
    a[0] = a[1] = 1
    b[1] = 1
    assert hamming(quantize(vec(a)), quantize(vec(b))) == 1
    assert hamming(quantize(vec(a)), quantize(vec(a))) == 0


# -- document codes ------------------------------------------------------------


def test_doc_code_is_the_scale_weighted_mean_sign():
    strong = dims()
    strong[0] = 10
    weak = dims()
    weak[0] = -1
    code = doc_code([vec(strong), vec(weak)])
    assert int.from_bytes(code, "little") & 1  # the stronger sign wins


def test_scale_is_respected_across_chunks():
    """A chunk with a large scale must not dominate purely by quantized value."""
    small_scale = Vec(q=tuple([100] + [0] * 255), scale=0.001, norm=100.0)
    large_scale = Vec(q=tuple([-1] + [0] * 255), scale=10.0, norm=1.0)
    assert not int.from_bytes(doc_code([small_scale, large_scale]), "little") & 1


def test_no_embeddable_chunk_yields_no_code():
    assert doc_code([None, None]) is None
    assert doc_code([]) is None


# -- the scan (unused until M2/M3, math still pinned) -------------------------


def test_prefilter_ranks_by_distance_and_truncates():
    near, far = dims(), dims()
    near[0] = 1
    far[0] = 1
    for i in range(1, 40):
        far[i] = 1
    codes = {"docs/near.md": quantize(vec(near)), "docs/far.md": quantize(vec(far))}
    query = quantize(vec(near))
    assert prefilter(query, codes, 2) == ["docs/near.md", "docs/far.md"]
    assert prefilter(query, codes, 1) == ["docs/near.md"]


def test_prefilter_ties_break_on_doc_id():
    """Equal distances must order reproducibly, or the candidate set drifts."""
    same = quantize(vec(dims()))
    codes = {"docs/z.md": same, "docs/a.md": same, "docs/m.md": same}
    assert prefilter(same, codes, 3) == ["docs/a.md", "docs/m.md", "docs/z.md"]


def test_prefilter_on_an_empty_corpus():
    assert prefilter(quantize(vec(dims())), {}, 500) == []
