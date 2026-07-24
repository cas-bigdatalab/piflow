from __future__ import annotations

import re
import unicodedata


def safe_name(value: str, *, max_len: int = 80) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    text = re.sub(r"[\/\\\s]+", "_", text)
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("._-")
    return text[:max_len] or "unnamed"
