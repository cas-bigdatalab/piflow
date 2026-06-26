import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

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

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 不可见/干扰字符集 ───────────────────────────────────────────────────
# 分类定义（所有码点转为单字符集合用于 translate 批量删除）

def _range_set(start: int, end: int) -> Set[int]:
    return set(range(start, end + 1))

_INVISIBLE_CODEPOINTS: Set[int] = set()

# BOM / 零宽不换行空格
_INVISIBLE_CODEPOINTS |= {0xFEFF}

# 零宽空格 / 零宽连接符 / 零宽非连接符
_INVISIBLE_CODEPOINTS |= {0x200B}  # ZERO WIDTH SPACE
_INVISIBLE_CODEPOINTS |= {0x2060}  # WORD JOINER

# 双向文本标记
_INVISIBLE_CODEPOINTS |= _range_set(0x200E, 0x200F)  # LRM, RLM
_INVISIBLE_CODEPOINTS |= _range_set(0x202A, 0x202E)  # 嵌入/覆盖/弹出
_INVISIBLE_CODEPOINTS |= _range_set(0x2066, 0x2069)  # 隔离

# 软连字符
_INVISIBLE_CODEPOINTS |= {0x00AD}

# C0 控制字符 (U+0000-U+001F)，保留 \t(0x09) \n(0x0A) \r(0x0D)
_INVISIBLE_CODEPOINTS |= _range_set(0x0000, 0x0008)
_INVISIBLE_CODEPOINTS |= _range_set(0x000B, 0x000C)
_INVISIBLE_CODEPOINTS |= _range_set(0x000E, 0x001F)

# 其它不可见字符
_INVISIBLE_CODEPOINTS |= {
    0x034F,  # COMBINING GRAPHEME JOINER
    0x061C,  # ARABIC LETTER MARK
    0x115F,  # HANGUL CHOSEONG FILLER
    0x1160,  # HANGUL JUNGSEONG FILLER
    0x17B4,  # KHMER VOWEL INHERENT AQ
    0x17B5,  # KHMER VOWEL INHERENT AA
    0x180E,  # MONGOLIAN VOWEL SEPARATOR
    0x2028,  # LINE SEPARATOR
    0x2029,  # PARAGRAPH SEPARATOR
    0x205F,  # MEDIUM MATHEMATICAL SPACE
    0x2061,  # FUNCTION APPLICATION
    0x2062,  # INVISIBLE TIMES
    0x2063,  # INVISIBLE SEPARATOR
    0x2064,  # INVISIBLE PLUS
    0x3164,  # HANGUL FILLER
    0xD800,  # Surrogate range start (incomplete — individual surrogates invalid)
    0xFFF9,  # INTERLINEAR ANNOTATION ANCHOR
    0xFFFA,  # INTERLINEAR ANNOTATION SEPARATOR
    0xFFFB,  # INTERLINEAR ANNOTATION TERMINATOR
}

# ZWJ / ZWNJ — 阿拉伯文/梵文等连字排版需要，可通过 --keep_format 保留
_ZWJ_ZWNJ = {0x200C, 0x200D}  # ZWNJ, ZWJ

# 构建删除映射表
def _build_delete_map(keep_format: bool) -> dict:
    codepoints = set(_INVISIBLE_CODEPOINTS)
    if not keep_format:
        codepoints |= _ZWJ_ZWNJ
    return {cp: None for cp in codepoints}  # None → 删除


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _clean_text(text: str, delete_map: dict) -> str:
    return text.translate(delete_map)


def clean_invisible(
    df: pd.DataFrame,
    cols: List[str],
    keep_format: bool,
) -> pd.DataFrame:
    delete_map = _build_delete_map(keep_format)
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _clean_text(str(x), delete_map) if not pd.isna(x) else x
        )
    return result


def run_cleaner(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    keep_format: bool,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        cols = _select_columns(df, None)

    cleaned = clean_invisible(df, cols=cols, keep_format=keep_format)

    write_structured_data(cleaned, output_path)
    total_cps = len(_INVISIBLE_CODEPOINTS)
    zwj_info = "（含ZWJ/ZWNJ）" if not keep_format else f"（保留ZWJ/ZWNJ，共 {total_cps + len(_ZWJ_ZWNJ)} 字符）"
    print(
        f"[OK] 不可见字符清洗完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   清理码点数: {total_cps} {zwj_info}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="不可见字符清洗：移除零宽空格、BOM、软连字符、双向控制符等不可见字符"
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
        "--keep_format", type=str_to_bool,
        help="保留零宽连接符/非连接符（ZWJ/ZWNJ），用于阿拉伯文/梵文排版",
    )
    args = parser.parse_args()
    run_cleaner(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        keep_format=args.keep_format,
    )


if __name__ == "__main__":
    main()
