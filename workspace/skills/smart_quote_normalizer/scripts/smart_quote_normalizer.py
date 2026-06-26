import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 1:1 字符映射（maketrans / translate 快速路径）──────────────────────
_SINGLE_MAP = {
    "“": '"',   # " LEFT DOUBLE QUOTATION MARK
    "”": '"',   # " RIGHT DOUBLE QUOTATION MARK
    "„": '"',   # „ DOUBLE LOW-9 QUOTATION MARK
    "«": '"',   # « LEFT-POINTING DOUBLE ANGLE QUOTATION
    "»": '"',   # » RIGHT-POINTING DOUBLE ANGLE QUOTATION
    "″": '"',   # ″ DOUBLE PRIME
    "‘": "'",   # ' LEFT SINGLE QUOTATION MARK
    "’": "'",   # ' RIGHT SINGLE QUOTATION MARK
    "‚": "'",   # ‚ SINGLE LOW-9 QUOTATION MARK
    "‹": "'",   # ‹ SINGLE LEFT-POINTING ANGLE
    "›": "'",   # › SINGLE RIGHT-POINTING ANGLE
    "′": "'",   # ′ PRIME
    "–": "-",   # – EN DASH
    "‒": "-",   # ‒ FIGURE DASH
    "‐": "-",   # ‐ HYPHEN (vs ASCII -)
    "‑": "-",   # ‑ NON-BREAKING HYPHEN
    "•": "*",   # • BULLET
    "⁄": "/",   # ⁄ FRACTION SLASH
    " ": " ",   #   NO-BREAK SPACE
    " ": "\n",  # LINE SEPARATOR
}

# ── 1:N 替换（str.replace 顺序处理）─────────────────────────────────────
_MULTI_REPLACE = [
    ("—", "--"),   # — EM DASH
    ("―", "--"),   # ― HORIZONTAL BAR
    ("…", "..."),  # … HORIZONTAL ELLIPSIS
    (" ", "\n\n"), # PARAGRAPH SEPARATOR
]

_SINGLE_TRANS = str.maketrans(_SINGLE_MAP)


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _normalize_text(text: str) -> str:
    s = text.translate(_SINGLE_TRANS)
    for old, new in _MULTI_REPLACE:
        s = s.replace(old, new)
    return s


def normalize_typographic(
    df: pd.DataFrame,
    cols: List[str],
) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _normalize_text(str(x)) if not pd.isna(x) else x
        )
    return result


def run_normalizer(input_path: str, output_path: str, text_columns: Optional[str]):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = normalize_typographic(df, cols=cols)
    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 智能引号/排版字符规范化完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   映射字符数: {len(_SINGLE_MAP)} + {len(_MULTI_REPLACE)} 多字符"
    )


def main():
    parser = argparse.ArgumentParser(
        description="智能引号/排版字符规范化：弯引号→直引号、长破折号→双连字符、省略号→三点等"
    )
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument(
        "--text_columns",
        required=False,
        default=None,
        help="处理的文本列，逗号分隔；默认全部字符串列",
    )
    args = parser.parse_args()
    run_normalizer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
    )


if __name__ == "__main__":
    main()
