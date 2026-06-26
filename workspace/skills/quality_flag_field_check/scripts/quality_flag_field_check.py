import argparse, sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _check_flag_field(
    df: pd.DataFrame,
    flag_field: str,
    valid_values: Optional[List[str]],
) -> tuple:
    """返回 (问题列表, 不合格行布尔索引)"""
    issues = []
    invalid_mask = pd.Series(False, index=df.index)

    # 1. 字段是否存在
    if flag_field not in df.columns:
        issues.append(f"[字段缺失] 质量标识字段 '{flag_field}' 不存在于表中，现有列: {list(df.columns)}")
        invalid_mask[:] = True
        return issues, invalid_mask

    # 2. 检查空值
    null_mask = df[flag_field].isna()
    null_count = null_mask.sum()
    if null_count > 0:
        issues.append(f"[空值] 字段 '{flag_field}' 有 {null_count} 行空值")
        invalid_mask |= null_mask

    # 3. 检查值规范性
    if valid_values:
        invalid_vals = df[~null_mask][flag_field].apply(
            lambda x: str(x).strip() not in valid_values
        )
        invalid_count = invalid_vals.sum()
        if invalid_count > 0:
            bad_samples = df[~null_mask][invalid_vals][flag_field].unique()[:5]
            issues.append(f"[非法值] 字段 '{flag_field}' 有 {invalid_count} 行不在合法值 {valid_values} 中，示例: {list(bad_samples)}")
            invalid_mask |= invalid_vals
    elif not null_mask.all():
        # 没有指定合法值，只要有非空值就视为存在
        pass

    return issues, invalid_mask


def run(input_path, output_path, flag_field_name, valid_values_arg, qc_mark, mark_field_name):
    df = read_structured_data(input_path)
    valid_values = [v.strip() for v in valid_values_arg.split(",") if v.strip()] if valid_values_arg else None

    issues, invalid_mask = _check_flag_field(df, flag_field_name, valid_values)

    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""
    if issues and invalid_mask.any():
        df.loc[invalid_mask, mark_field] = qc_mark
        print(f"[QC FAIL] 质量标识字段校验未通过 ({len(issues)} 项问题):")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"[QC PASS] 质量标识字段 '{flag_field_name}' 校验通过")

    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="质量标识字段检测：检查质量标识字段的存在性、规范性")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--flag_field_name", required=True, help="质量标识字段名")
    p.add_argument("--valid_values", default=None, help="合法值，逗号分隔（如 PASS,FAIL,WARN）")
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.flag_field_name,
        args.valid_values, args.qc_mark, args.mark_field_name)


if __name__ == "__main__":
    main()
