import argparse, sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 括号类符号 → 半角映射 ────────────────────────────────────────────────
_BRACKET_MAP = {
    "【": "[",  "】": "]",
    "「": '"',  "」": '"',
    "『": '"',  "』": '"',
    "《": "<",  "》": ">",
    "（": "(",  "）": ")",
    "〔": "[",  "〕": "]",
    "｛": "{",  "｝": "}",
    "［": "[",  "］": "]",
    "〈": "<",  "〉": ">",
    "｟": "(",  "｠": ")",
}

_BRACKET_TRANS = str.maketrans(_BRACKET_MAP)


def _normalize(text: str) -> str:
    return text.translate(_BRACKET_TRANS)


def _select_columns(df, text_columns):
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def run(input_path, output_path, text_columns):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns) or _select_columns(df, None)
    for col in cols:
        df[col] = df[col].apply(
            lambda x: _normalize(str(x)) if not pd.isna(x) else x
        )
    write_structured_data(df, output_path)
    print(f"[OK] 括号类符号统一完成 -> {output_path}\n   列: {cols}, 映射: {len(_BRACKET_MAP)} 对")


def main():
    p = argparse.ArgumentParser(description="括号类符号统一：中文/全角括号转为半角括号")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--text_columns", default=None)
    args = p.parse_args()
    run(args.input_path, args.output_path, args.text_columns)


if __name__ == "__main__":
    main()
