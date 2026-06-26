import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
def str_to_bool(value):
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── Unicode 连字 → ASCII 映射 ──────────────────────────────────────────
LIGATURE_MAP = {
    "ﬀ": "ff",   # ﬀ
    "ﬁ": "fi",   # ﬁ
    "ﬂ": "fl",   # ﬂ
    "ﬃ": "ffi",  # ﬃ
    "ﬄ": "ffl",  # ﬄ
    "ﬅ": "ft",   # ﬅ
    "ﬆ": "st",   # ﬆ
}

# ── 正则 ───────────────────────────────────────────────────────────────
# 断行连字符：word_char + '-' + 换行 + 可选空格 + word_char
DEHYPHENATE_RE = re.compile(r"(\w)-\s*\n\s*(\w)")

# 独立页码行匹配
PAGE_NUM_RE = re.compile(
    r"^\s*(?:\d{1,4}|[ivxlcdm]{1,8})\s*$",
    re.IGNORECASE,
)
PAGE_NUM_DASHED_RE = re.compile(
    r"^\s*-\s*(?:\d{1,4}|[ivxlcdm]{1,8})\s*-\s*$",
    re.IGNORECASE,
)

_IS_PAGE_NUM_RE = [PAGE_NUM_RE, PAGE_NUM_DASHED_RE]


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _is_page_number_line(line: str) -> bool:
    return any(pat.match(line) for pat in _IS_PAGE_NUM_RE)


def _clean_text(
    text: str,
    dehyphenate: bool,
    strip_page_numbers: bool,
    normalize_ligatures: bool,
    header_re: Optional[re.Pattern],
    footer_re: Optional[re.Pattern],
) -> str:
    s = text

    # 1. 连字归一化（在 dehyphenation 之前，避免干扰匹配）
    if normalize_ligatures:
        s = s.translate(str.maketrans(LIGATURE_MAP))

    # 2. 断行连字符拼接
    if dehyphenate:
        s = DEHYPHENATE_RE.sub(r"\1\2", s)

    # 3. 逐行处理：去页码 + 去页眉页脚
    if strip_page_numbers or header_re or footer_re:
        lines = s.splitlines()
        kept = []
        for line in lines:
            # 去除独立页码行
            if strip_page_numbers and _is_page_number_line(line):
                continue
            # 去除匹配页眉模式的行
            if header_re and header_re.search(line):
                continue
            # 去除匹配页脚模式的行
            if footer_re and footer_re.search(line):
                continue
            kept.append(line)
        s = "\n".join(kept)

    return s


def clean_artifacts(
    df: pd.DataFrame,
    cols: List[str],
    dehyphenate: bool,
    strip_page_numbers: bool,
    normalize_ligatures: bool,
    header_pattern: Optional[str],
    footer_pattern: Optional[str],
) -> pd.DataFrame:
    header_re = re.compile(header_pattern) if header_pattern else None
    footer_re = re.compile(footer_pattern) if footer_pattern else None

    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _clean_text(
                str(x), dehyphenate, strip_page_numbers,
                normalize_ligatures, header_re, footer_re,
            ) if not pd.isna(x) else x
        )
    return result


def run_cleaner(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    dehyphenate: bool,
    strip_page_numbers: bool,
    normalize_ligatures: bool,
    header_pattern: Optional[str],
    footer_pattern: Optional[str],
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    cleaned = clean_artifacts(
        df, cols=cols,
        dehyphenate=dehyphenate,
        strip_page_numbers=strip_page_numbers,
        normalize_ligatures=normalize_ligatures,
        header_pattern=header_pattern,
        footer_pattern=footer_pattern,
    )

    write_structured_data(cleaned, output_path)
    flags = []
    if dehyphenate:
        flags.append("dehyphenate")
    if strip_page_numbers:
        flags.append("strip_page_numbers")
    if normalize_ligatures:
        flags.append("normalize_ligatures")
    if header_pattern:
        flags.append(f"header_pattern={header_pattern!r}")
    if footer_pattern:
        flags.append(f"footer_pattern={footer_pattern!r}")

    print(
        f"[OK] PDF/OCR伪影清洗完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   启用: {flags or '无'}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="PDF/OCR伪影清洗：断行连字符拼接、去页码、连字归一化、页眉页脚去除"
    )
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument(
        "--text_columns",
        required=False,
        default=None,
        help="处理的文本列，逗号分隔；默认全部字符串列",
    )
    parser.add_argument(
        "--no_dehyphenate", type=str_to_bool,
        help="关闭断行连字符拼接",
    )
    parser.add_argument(
        "--no_strip_page_numbers", type=str_to_bool,
        help="关闭页码去除",
    )
    parser.add_argument(
        "--no_normalize_ligatures", type=str_to_bool,
        help="关闭Unicode连字归一化",
    )
    parser.add_argument(
        "--header_pattern",
        required=False,
        default=None,
        help="匹配页眉行的正则表达式",
    )
    parser.add_argument(
        "--footer_pattern",
        required=False,
        default=None,
        help="匹配页脚行的正则表达式",
    )

    args = parser.parse_args()
    run_cleaner(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        dehyphenate=not args.no_dehyphenate,
        strip_page_numbers=not args.no_strip_page_numbers,
        normalize_ligatures=not args.no_normalize_ligatures,
        header_pattern=args.header_pattern,
        footer_pattern=args.footer_pattern,
    )


if __name__ == "__main__":
    main()
