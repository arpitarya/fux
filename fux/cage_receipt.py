"""Optional cage integration — emit a token-saving receipt, no-op if cage absent."""
from __future__ import annotations


def toks(text: str) -> int:
    return max(0, round(len(text) / 4))


def emit(tool: str, raw_alternative: int, actual: int, *, task: str = "",
         op: str = "", confidence: float = 0.7) -> None:
    """File a 'tokens' receipt with cage. Silent if cage isn't installed/usable."""
    if actual >= raw_alternative:          # no saving to claim — stay honest
        return
    try:
        from cage import record_receipt
        record_receipt(tool=tool, unit="tokens", raw_alternative=raw_alternative,
                       actual=actual, method="modeled", confidence=confidence,
                       task=task, meta={"op": op})
    except Exception:                       # cage missing or any error → no-op
        return
