"""FuxVec — bundled static-embedding runtime (stdlib-only) + sign-quantized
codes for the ledger's `code` property. Ported from `archive/v0.26/src/fux/embed/`
(model.py, fuxvec.py); `store.py` (a chunk-vector *cache* file for the old
architecture) is not ported — M1's `code` lives directly in each ledger
record, so there is nothing to cache.
"""

from .fuxvec import CODE_BYTES, doc_code, hamming, quantize
from .model import MAX_TOKENS, Model, Vec, get_model

__all__ = ["CODE_BYTES", "MAX_TOKENS", "Model", "Vec", "doc_code", "get_model", "hamming", "quantize"]
