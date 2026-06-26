import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# 数学符号归一
MATH_SYMBOLS = {
    "−": "-",  # minus
    "–": "-",
    "—": "-",
    "±": "+-",
    "×": "*",
    "÷": "/",
    "∙": "*",
    "·": "*",
    "＝": "=",
    "＋": "+",
    "－": "-",
    "＊": "*",
    "／": "/",
    "（": "(",
    "）": ")",
    "［": "[",
    "］": "]",
    "｛": "{",
    "｝": "}",
}

# 化学/反应箭头归一
ARROW_MAP = {
    "→": "->",
    "⇒": "->",
    "➡": "->",
    "⇌": "<->",
    "↔": "<->",
    "⇄": "<->",
}
ARROW_RE = re.compile("|".join(map(re.escape, ARROW_MAP.keys())))

SUPERSCRIPT_MAP = str.maketrans({
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-",
})
SUBSCRIPT_MAP = str.maketrans({
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-",
})
SUP_RE = re.compile("[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻]+")
SUB_RE = re.compile("[₀₁₂₃₄₅₆₇₈₉₊₋]+")
MULTI_SPACE_RE = re.compile(r"\s{2,}")

_FULLWIDTH_ASCII_MAP = {chr(code): chr(code - 0xFEE0) for code in range(0xFF01, 0xFF5F)}
_FULLWIDTH_ASCII_MAP["　"] = " "
FULLWIDTH_ASCII_TRANS = str.maketrans(_FULLWIDTH_ASCII_MAP)


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _normalize_sup_sub(s: str) -> str:
    s = SUP_RE.sub(lambda m: "^" + m.group(0).translate(SUPERSCRIPT_MAP), s)
    s = SUB_RE.sub(lambda m: "_" + m.group(0).translate(SUBSCRIPT_MAP), s)
    return s


def _normalize_symbols(s: str) -> str:
    for k, v in MATH_SYMBOLS.items():
        s = s.replace(k, v)
    s = ARROW_RE.sub(lambda m: ARROW_MAP.get(m.group(0), m.group(0)), s)
    return s


def _normalize_spacing(s: str) -> str:
    # 去多余空格，保留单个空格分隔
    s = MULTI_SPACE_RE.sub(" ", s)
    return s.strip()


def _normalize_fullwidth_ascii(s: str) -> str:
    return s.translate(FULLWIDTH_ASCII_TRANS)


def normalize_text(s: str) -> str:
    s = _normalize_fullwidth_ascii(s)
    s = _normalize_symbols(s)
    s = _normalize_sup_sub(s)
    s = _normalize_spacing(s)
    return s


def normalize_dataframe(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(lambda x: normalize_text(str(x)) if not pd.isna(x) else x)
    return result


def run_normalizer(input_path: str, output_path: str, text_columns: Optional[str]):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = normalize_dataframe(df, cols)

    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 科学公式/化学式规整完成 -> {output_path}\n"
        f"   文本列: {cols}"
    )


def main():
    parser = argparse.ArgumentParser(description="科学公式/化学式规整：统一符号、上下标、反应箭头与空格")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--text_columns", required=False, default=None, help="处理的文本列，逗号分隔；默认全部字符串列")

    args = parser.parse_args()
    run_normalizer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
    )


if __name__ == "__main__":
    main()
