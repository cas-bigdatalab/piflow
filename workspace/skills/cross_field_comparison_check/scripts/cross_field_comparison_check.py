import argparse, sys, operator
from pathlib import Path
from typing import List, Tuple
import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq, "!=": operator.ne}

def _parse(raw: str) -> List[Tuple[str, str, str]]:
    result = []
    for item in raw.split("|"):
        parts = item.strip().split(",")
        if len(parts) == 3:
            result.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))
    return result

def run(input_path, output_path, constraints, qc_mark, mark_field_name):
    df = read_structured_data(input_path)
    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""

    parsed = _parse(constraints)
    invalid_mask = pd.Series(False, index=df.index)
    issues = []

    for left, op, right in parsed:
        if op not in OPS:
            issues.append(f"[运算符错误] 不支持: {op}")
            continue
        missing = [c for c in [left, right] if c not in df.columns]
        if missing:
            issues.append(f"[字段缺失] {missing}")
            continue
        lv, rv = pd.to_numeric(df[left], errors="coerce"), pd.to_numeric(df[right], errors="coerce")
        op_func = OPS[op]
        # 逐行比较，跳过 NaN
        mask = pd.Series(False, index=df.index)
        for idx in df.index:
            a, b = lv.at[idx], rv.at[idx]
            if pd.isna(a) or pd.isna(b):
                continue
            if not op_func(a, b):
                mask.at[idx] = True
        if mask.any():
            issues.append(f"[{left} {op} {right}] {mask.sum()} 行违反约束")
            invalid_mask |= mask

    if invalid_mask.any():
        df.loc[invalid_mask, mark_field] = qc_mark
        print(f"[QC FAIL] 跨字段比较未通过 ({len(issues)} 项):")
        for i in issues: print(f"  {i}")
    else:
        print(f"[QC PASS] 所有跨字段约束通过")
    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")

def main():
    p = argparse.ArgumentParser(description="跨字段比较校验")
    p.add_argument("--input_path", required=True); p.add_argument("--output_path", required=True)
    p.add_argument("--constraints", required=True, help="左字段,运算符,右字段 逗号分隔")
    p.add_argument("--qc_mark", required=True); p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.constraints, args.qc_mark, args.mark_field_name)

if __name__ == "__main__":
    main()
