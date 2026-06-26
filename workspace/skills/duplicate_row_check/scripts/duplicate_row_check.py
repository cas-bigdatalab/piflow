import argparse, sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def run(input_path, output_path, dup_columns, qc_mark, mark_field_name):
    df = read_structured_data(input_path)
    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""

    cols = [c.strip() for c in dup_columns.split(",") if c.strip()] if dup_columns else None
    subset = cols if cols else list(df.columns)
    subset = [c for c in subset if c in df.columns]

    dup_mask = df.duplicated(subset=subset, keep="first")
    if dup_mask.any():
        df.loc[dup_mask, mark_field] = qc_mark
        print(f"[QC FAIL] 发现 {dup_mask.sum()} 行重复 (检测列: {subset})")
    else:
        print(f"[QC PASS] 未发现重复行")

    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="结构化表格重复行检测")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--dup_columns", default=None, help="检测列，逗号分隔")
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.dup_columns, args.qc_mark, args.mark_field_name)


if __name__ == "__main__":
    main()
