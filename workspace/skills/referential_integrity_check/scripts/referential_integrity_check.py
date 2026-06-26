import argparse, sys
from pathlib import Path
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def run(input_path, output_path, check_field, reference_path, reference_column, qc_mark, mark_field_name):
    df = read_structured_data(input_path)
    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""

    if reference_path:
        ref_df = read_structured_data(reference_path)
    else:
        ref_df = df

    if check_field not in df.columns:
        print(f"[ERROR] 检查字段 '{check_field}' 不存在")
        sys.exit(1)
    if reference_column not in ref_df.columns:
        print(f"[ERROR] 参考列 '{reference_column}' 不存在")
        sys.exit(1)

    ref_values = set(ref_df[reference_column].dropna().astype(str).str.strip())
    check_vals = df[check_field].astype(str).str.strip()
    orphan_mask = ~check_vals.isin(ref_values) & (check_vals != "nan") & (check_vals != "")

    if orphan_mask.any():
        df.loc[orphan_mask, mark_field] = qc_mark
        samples = df.loc[orphan_mask, check_field].astype(str).unique()[:5]
        print(f"[QC FAIL] 引用完整性校验未通过: {int(orphan_mask.sum())} 行孤立值，示例: {list(samples)}")
    else:
        print(f"[QC PASS] 所有 {check_field} 的值均在 {reference_column} 中存在")

    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="引用完整性校验")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--check_field", required=True)
    p.add_argument("--reference_path", default=None)
    p.add_argument("--reference_column", required=True)
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.check_field, args.reference_path, args.reference_column, args.qc_mark, args.mark_field_name)


if __name__ == "__main__":
    main()
