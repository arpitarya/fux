"""Utilities for parsing raw telemetry frames."""


def parse_frame(raw: bytes) -> dict:
    """Parse one telemetry frame into a dict (little-endian, 16-byte header)."""
    return {"length": len(raw), "kind": raw[:1]}
