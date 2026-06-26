import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _row_reason(row: pd.Series, cols: List[str], min_chars: int, max_chars: int, min_lines: int, max_lines: int) -> str:
    reasons = []
    for col in cols:
        val = row[col]
        if pd.isna(val):
            continue
        s = str(val)
        char_len = len(s)
        line_count = s.count("\n") + 1
        if char_len < min_chars:
            reasons.append(f"{col}:len<{min_chars}")
        if max_chars > 0 and char_len > max_chars:
            reasons.append(f"{col}:len>{max_chars}")
        if line_count < min_lines:
            reasons.append(f"{col}:lines<{min_lines}")
        if max_lines > 0 and line_count > max_lines:
            reasons.append(f"{col}:lines>{max_lines}")
    return ";".join(reasons)


def filter_low_info(df: pd.DataFrame, cols: List[str], min_chars: int, max_chars: int, min_lines: int, max_lines: int) -> pd.DataFrame:
    reasons = df.apply(
        lambda row: _row_reason(row, cols, min_chars, max_chars, min_lines, max_lines), axis=1
    )
    mask = reasons == ""
    filtered = df.copy()
    filtered["filter_reason"] = reasons
    # 仅保留未触发的行
    return filtered[mask].drop(columns=["filter_reason"]).reset_index(drop=True)


def run_filter(input_path: str, output_path: str, text_columns: Optional[str], min_chars: int, max_chars: int, min_lines: int, max_lines: int):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    filtered = filter_low_info(df, cols, min_chars, max_chars, min_lines, max_lines)

    write_structured_data(filtered, output_path)
    print(
        f"[OK] 低信息量过滤完成 -> {output_path}\n"
        f"   文本列: {cols}\n"
        f"   输出行数: {len(filtered)} / 原始行数: {len(df)}"
    )


def main():
    parser = argparse.ArgumentParser(description="低信息量过滤：按字数/行数上下限过滤文本样本")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--text_columns", required=False, default=None, help="检测的文本列，逗号分隔；默认全部字符串列")
    parser.add_argument("--min_chars", type=int, default=10, help="最小字符数，默认 10")
    parser.add_argument("--max_chars", type=int, default=2000, help="最大字符数（0 表示不限），默认 2000")
    parser.add_argument("--min_lines", type=int, default=1, help="最小行数，默认 1")
    parser.add_argument("--max_lines", type=int, default=200, help="最大行数（0 表示不限），默认 200")

    args = parser.parse_args()
    run_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        min_chars=args.min_chars,
        max_chars=args.max_chars,
        min_lines=args.min_lines,
        max_lines=args.max_lines,
    )


if __name__ == "__main__":
    main()
