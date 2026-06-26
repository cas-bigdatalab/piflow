import argparse, sys
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _check_gradual_change(
    df: pd.DataFrame,
    check_field: str,
    time_field: str,
    time_format: str,
    jump_threshold: Optional[float],
    window_size: int,
    oscillation_limit: int,
) -> tuple:
    issues: List[str] = []
    invalid_mask = pd.Series(False, index=df.index)

    if check_field not in df.columns:
        issues.append(f"[字段缺失] 检测字段 '{check_field}' 不存在")
        invalid_mask[:] = True
        return issues, invalid_mask
    if time_field not in df.columns:
        issues.append(f"[字段缺失] 时间字段 '{time_field}' 不存在")
        invalid_mask[:] = True
        return issues, invalid_mask

    # 按时间排序
    try:
        df_sorted = df.copy()
        df_sorted[time_field] = pd.to_datetime(df_sorted[time_field], format=time_format, errors="coerce")
        df_sorted = df_sorted.dropna(subset=[time_field])
        df_sorted = df_sorted.sort_values(time_field).reset_index(drop=True)
    except Exception as e:
        issues.append(f"[解析错误] 时间字段解析失败: {e}")
        invalid_mask[:] = True
        return issues, invalid_mask

    values = pd.to_numeric(df_sorted[check_field], errors="coerce")
    n = len(values)

    # 1. 突变跳点检测
    if jump_threshold is not None and n > 1:
        diffs = values.diff().abs()
        jump_mask = diffs > jump_threshold
        jump_count = jump_mask.sum()
        if jump_count > 0:
            issues.append(f"[突变跳点] {jump_count} 处相邻变化超过阈值 {jump_threshold}")
            # 标记跳点和前一个点
            jump_indices = set()
            for i in range(1, n):
                if diffs.iloc[i] > jump_threshold:
                    jump_indices.add(i)
                    jump_indices.add(i - 1)
            # 映射回原始索引
            for ji in jump_indices:
                orig_idx = df_sorted.index[ji]
                invalid_mask.loc[orig_idx] = True

    # 2. 方向振荡检测
    osc_flagged = 0
    if window_size > 1 and n > window_size:
        osc_mask = pd.Series(False, index=df_sorted.index)
        signs = np.sign(values.diff().fillna(0))
        for i in range(n - window_size + 1):
            window_signs = signs.iloc[i:i + window_size]
            reversals = (window_signs.diff().abs() > 0).sum() - 1
            if reversals > oscillation_limit:
                for j in range(window_size):
                    osc_mask.iloc[i + j] = True
        osc_count = osc_mask.sum()
        if osc_count > 0:
            issues.append(
                f"[方向振荡] 存在振荡异常（{window_size} 点窗口内反转超过 {oscillation_limit} 次），"
                f"共标记 {osc_count} 个数据点"
            )
            invalid_mask |= osc_mask

    return issues, invalid_mask


def run(input_path, output_path, check_field, time_field, time_format,
        jump_threshold, window_size, oscillation_limit, qc_mark, mark_field_name):
    df = read_structured_data(input_path)

    issues, invalid_mask = _check_gradual_change(
        df, check_field, time_field, time_format,
        jump_threshold, window_size or 5, oscillation_limit or 2,
    )

    mark_field = mark_field_name or "QC0000"
    df[mark_field] = ""
    if issues and invalid_mask.any():
        df.loc[invalid_mask, mark_field] = qc_mark
        print(f"[QC FAIL] 时序平缓性检测未通过 ({len(issues)} 项问题):")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"[QC PASS] 时序平缓性检测通过")

    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="时序平缓性检测：突变跳点 + 方向振荡")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--check_field", required=True, help="检测字段名")
    p.add_argument("--time_field", required=True, help="时间字段名")
    p.add_argument("--time_format", required=True, help="时间格式")
    p.add_argument("--jump_threshold", type=float, default=None, help="突变跳点阈值")
    p.add_argument("--window_size", type=int, default=5, help="振荡窗口大小")
    p.add_argument("--oscillation_limit", type=int, default=2, help="窗口内最大反转次数")
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(args.input_path, args.output_path, args.check_field, args.time_field,
        args.time_format, args.jump_threshold, args.window_size,
        args.oscillation_limit, args.qc_mark, args.mark_field_name)


if __name__ == "__main__":
    main()
