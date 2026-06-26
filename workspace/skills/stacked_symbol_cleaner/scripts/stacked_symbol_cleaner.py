import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 装饰符号字符集 ──────────────────────────────────────────────────────
_DECOR_CHARS = r"\-*=_~#\+\.\/\\\^<>!@\$%&"

# 连续重复符号行：如 ====  ****  ----  ~~~~
_REPEAT_RE_TMPL = r"^\s*([{chars}])\1{{{min_r},}}\s*$"

# 带空格/交替符号行：如 * * * *  -=-=-=-  _._._._
_SPACED_RE_TMPL = (
    r"^\s*"                          # 行首空格
    r"([{chars}])\s*"                # 符号+可选空格
    r"(\1\s*)"                       # 重复
    r"{{{min_r},}}"                   # 至少 min_repeat 次
    r"$"
)
_ALTERNATING_RE_TMPL = (
    r"^\s*"
    r"([{chars}])"                   # 符号1
    r"([{chars}])"                   # 符号2（不同）
    r"(\1\2\s*)"                     # 交替对
    r"{{{min_pairs},}}"               # 至少 min_pairs 对
    r"\1?"                           # 可选：末尾多余一个符号1（奇数长度）
    r"\s*$"
)


def _build_patterns(min_repeat: int) -> List[re.Pattern]:
    """构建匹配模式列表"""
    patterns = []
    min_r = max(2, min_repeat - 1)  # 正则重复次数

    # 1. 连续重复
    patterns.append(re.compile(
        _REPEAT_RE_TMPL.format(chars=_DECOR_CHARS, min_r=min_r)
    ))

    # 2. 带空格
    patterns.append(re.compile(
        _SPACED_RE_TMPL.format(chars=_DECOR_CHARS, min_r=min_r)
    ))

    # 3. 交替符号 (至少2对)
    min_pairs = max(1, min_repeat // 2 - 1)
    patterns.append(re.compile(
        _ALTERNATING_RE_TMPL.format(chars=_DECOR_CHARS, min_pairs=min_pairs)
    ))

    return patterns


def _is_decoration_line(line: str, patterns: List[re.Pattern]) -> bool:
    return any(p.match(line) for p in patterns)


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _clean_text(text: str, patterns: List[re.Pattern]) -> str:
    lines = text.splitlines()
    kept = [line for line in lines if not _is_decoration_line(line, patterns)]
    return "\n".join(kept)


def clean_stacked_symbols(
    df: pd.DataFrame,
    cols: List[str],
    min_repeat: int,
) -> pd.DataFrame:
    patterns = _build_patterns(min_repeat)
    result = df.copy()
    for col in cols:
        result[col] = result[col].apply(
            lambda x: _clean_text(str(x), patterns) if not pd.isna(x) else x
        )
    return result


def run_cleaner(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    min_repeat: int,
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        cols = _select_columns(df, None)

    cleaned = clean_stacked_symbols(df, cols=cols, min_repeat=min_repeat)
    write_structured_data(cleaned, output_path)
    print(
        f"[OK] 堆叠符号清洗完成 -> {output_path}\n"
        f"   文本列: {cols}, min_repeat={min_repeat}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="堆叠符号清洗：去除纯符号装饰行（====、****、----、~~~~ 等）"
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
        "--min_repeat",
        required=False,
        type=int,
        default=4,
        help="最小连续重复次数（默认 4）",
    )
    args = parser.parse_args()
    run_cleaner(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        min_repeat=args.min_repeat,
    )


if __name__ == "__main__":
    main()
