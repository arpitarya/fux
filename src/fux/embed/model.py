"""Bundled-model runtime: stdlib-only tokenize → lookup → mean-pool → int8 sim.

Loads `data/model.bin` (packed by tools/distill; format documented there),
reimplements the teacher's tokenizer — BertNormalizer (clean, CJK spacing,
lowercase + accent-strip) + Bert pre-tokenization + WordPiece — in pure
stdlib, and does similarity as exact int8 dot products (sum in int, scale
once) so results are identical across platforms. No numpy, no downloads,
ever (packaged-model compare doc). Loading is lazy: lexical-only paths never
pay for it.
"""

from __future__ import annotations

import re
import struct
import unicodedata
from array import array
from dataclasses import dataclass
from math import sqrt
from pathlib import Path

from ..errors import FuxError

MAGIC = b"FUXEMB1\0"
DATA_PATH = Path(__file__).parent / "data" / "model.bin"
SPECIALS = {"[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"}
MAX_TOKENS = 1024  # truncation policy for very long chunks (ADR 0006)

_PUNCT_ASCII = set(range(33, 48)) | set(range(58, 65)) | set(range(91, 97)) | set(range(123, 127))
_SPECIAL_RE = re.compile("(" + "|".join(re.escape(t) for t in sorted(SPECIALS)) + ")")
_CJK_RANGES = (
    (0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F),
    (0x2B740, 0x2B81F), (0x2B820, 0x2CEAF), (0xF900, 0xFAFF), (0x2F800, 0x2FA1F),
)


@dataclass(frozen=True)
class Vec:
    """A quantized embedding: int8 components, one scale, precomputed norm."""

    q: tuple[int, ...]
    scale: float
    norm: float


class Model:
    def __init__(self, path: Path = DATA_PATH):
        if not path.is_file():
            raise FuxError(
                "embedding model not bundled — install the packaged wheel, or build "
                "it with tools/distill/distill.py (lexical search still works: --lexical-only)"
            )
        try:
            self._load(path)
        except (struct.error, ValueError, AssertionError) as exc:
            raise FuxError(f"embedding model is corrupt ({exc}) — rebuild via tools/distill") from exc

    def _load(self, path: Path) -> None:
        data = path.read_bytes()
        assert data[:8] == MAGIC, "bad magic"
        version, vocab_size, dim = struct.unpack_from("<III", data, 8)
        assert version == 1, f"unsupported bundle version {version}"
        self.vocab_size, self.dim = vocab_size, dim
        offset = 20
        self.vocab: list[str] = []
        for _ in range(vocab_size):
            (length,) = struct.unpack_from("<H", data, offset)
            offset += 2
            self.vocab.append(data[offset : offset + length].decode("utf-8"))
            offset += length
        self.scales = array("f")
        self.scales.frombytes(data[offset : offset + 4 * vocab_size])
        offset += 4 * vocab_size
        self.matrix = array("b")
        self.matrix.frombytes(data[offset : offset + vocab_size * dim])
        assert len(self.matrix) == vocab_size * dim, "truncated matrix"
        self.token_to_id = {token: i for i, token in enumerate(self.vocab)}
        self._special_ids = {self.token_to_id[t] for t in SPECIALS if t in self.token_to_id}
        self._unk_id = self.token_to_id.get("[UNK]", -1)

    def row(self, token_id: int) -> array:
        start = token_id * self.dim
        return self.matrix[start : start + self.dim]

    # -- tokenizer (BertNormalizer + BertPreTokenizer + WordPiece) ---------

    def tokenize(self, text: str) -> list[int]:
        # added special tokens match atomically, pre-normalization (HF behaviour)
        ids: list[int] = []
        for segment in _SPECIAL_RE.split(text):
            if segment in SPECIALS:
                ids.append(self.token_to_id.get(segment, self._unk_id))
                continue
            for word in _pre_tokenize(_normalize(segment)):
                ids.extend(self._wordpiece(word))
        return ids

    def _wordpiece(self, word: str) -> list[int]:
        if len(word) > 100:
            return [self._unk_id]
        pieces: list[int] = []
        start = 0
        while start < len(word):
            end = len(word)
            found = None
            while end > start:
                piece = ("##" if start else "") + word[start:end]
                token_id = self.token_to_id.get(piece)
                if token_id is not None:
                    found = token_id
                    break
                end -= 1
            if found is None:
                return [self._unk_id]
            pieces.append(found)
            start = end
        return pieces

    # -- embedding ---------------------------------------------------------

    def embed(self, text: str) -> Vec | None:
        ids = [
            i
            for i in self.tokenize(text)[:MAX_TOKENS]
            if i >= 0 and i != self._unk_id and i not in self._special_ids
        ]
        if not ids:
            return None
        dim = self.dim
        acc = [0.0] * dim
        for token_id in ids:  # fixed order: deterministic float accumulation
            scale = self.scales[token_id]
            start = token_id * dim
            row = self.matrix
            for d in range(dim):
                acc[d] += scale * row[start + d]
        n = float(len(ids))
        maxabs = max(abs(v) for v in acc)
        if maxabs == 0.0:
            return None
        scale = maxabs / (127.0 * n)  # fold the mean into the scale
        q = tuple(min(127, max(-127, round(v / (scale * n)))) for v in acc)
        norm = sqrt(sum(x * x for x in q))
        if norm == 0.0:
            return None
        return Vec(q=q, scale=scale, norm=norm)

    @staticmethod
    def similarity(a: Vec, b: Vec) -> float:
        """Cosine over int8 components: exact integer dot, scaled once."""
        dot = 0
        for x, y in zip(a.q, b.q):
            dot += x * y
        return dot / (a.norm * b.norm)


def _normalize(text: str) -> str:
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if cp == 0 or cp == 0xFFFD or _is_control(ch):
            continue
        if _is_whitespace(ch):
            out.append(" ")
        elif any(lo <= cp <= hi for lo, hi in _CJK_RANGES):
            out.append(f" {ch} ")
        else:
            out.append(ch)
    lowered = "".join(out).lower()
    return "".join(
        ch for ch in unicodedata.normalize("NFD", lowered) if unicodedata.category(ch) != "Mn"
    )


def _pre_tokenize(text: str) -> list[str]:
    words: list[str] = []
    for chunk in text.split():
        buf = ""
        for ch in chunk:
            if _is_punct(ch):
                if buf:
                    words.append(buf)
                    buf = ""
                words.append(ch)
            else:
                buf += ch
        if buf:
            words.append(buf)
    return words


def _is_control(ch: str) -> bool:
    if ch in ("\t", "\n", "\r"):
        return False
    return unicodedata.category(ch).startswith("C")


def _is_whitespace(ch: str) -> bool:
    return ch in ("\t", "\n", "\r", " ") or unicodedata.category(ch) == "Zs"


def _is_punct(ch: str) -> bool:
    return ord(ch) in _PUNCT_ASCII or unicodedata.category(ch).startswith("P")


_model: Model | None = None
_model_missing = False


def get_model() -> Model | None:
    """Lazy singleton; None when the bundle isn't shipped (source installs)."""
    global _model, _model_missing
    if _model is None and not _model_missing:
        if not DATA_PATH.is_file():
            _model_missing = True
            return None
        _model = Model()
    return _model
