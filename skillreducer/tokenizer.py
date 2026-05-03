from __future__ import annotations

import re


_ENCODER = None
_ENCODER_READY = False


def count_tokens(text: str) -> int:
    """Count tokens with tiktoken when available, otherwise use a stable approximation."""
    global _ENCODER, _ENCODER_READY
    if not text:
        return 0
    if not _ENCODER_READY:
        try:
            import tiktoken  # type: ignore

            _ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _ENCODER = None
        _ENCODER_READY = True
    if _ENCODER is not None:
        return len(_ENCODER.encode(text))
    # Approximate English/code-ish tokenization. This is deterministic and dependency-free.
    pieces = re.findall(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]", text)
    return len(pieces)


def compression_ratio(original: str, compressed: str) -> float:
    original_tokens = max(count_tokens(original), 1)
    return 1.0 - (count_tokens(compressed) / original_tokens)

