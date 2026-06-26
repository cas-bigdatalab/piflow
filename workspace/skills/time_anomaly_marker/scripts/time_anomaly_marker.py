import argparse
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _select_numeric_columns(df: pd.DataFrame, numeric_columns: Optional[str]) -> List[str]:
    if numeric_columns:
        requested = [c.strip() for c in numeric_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        cols = [c for c in requested if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
        if not cols:
            print("[WARN] 指定列中无数值列，将不做标记。")
        return cols
    # 默认选择所有数值型列
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _mark_anomalies(df: pd.DataFrame, cols: List[str], z_threshold: float, diff_threshold: float) -> pd.DataFrame:
    flagged = pd.Series(False, index=df.index)
    reasons = pd.Series([[] for _ in range(len(df))], index=df.index, dtype=object)

    for col in cols:
        series = pd.to_numeric(df[col], errors="coerce")
        # 全部 NaN 则跳过
        if series.notna().sum() == 0:
            continue

        # 全局 Z-Score 异常
        std = series.std()
        if pd.notna(std) and std > 0:
            z_mask = (series - series.mean()).abs() > z_threshold * std
            if z_mask.any():
                flagged |= z_mask
                for idx in series.index[z_mask]:
                    reasons.at[idx].append(f"z>{z_threshold} in {col}")

        # 差分异常（尖峰/突变）
        diff = series.diff()
        diff_std = diff.std()
        if pd.notna(diff_std) and diff_std > 0:
            spike_mask = diff.abs() > diff_threshold * diff_std
            # 对于突变，标记当前行
            if spike_mask.any():
                flagged |= spike_mask
                for idx in series.index[spike_mask]:
                    reasons.at[idx].append(f"diff>{diff_threshold}σ in {col}")

    df_out = df.copy()
    df_out["anomaly_flag"] = flagged
    df_out["anomaly_reasons"] = reasons.apply(lambda lst: "; ".join(lst) if lst else "")
    return df_out


def time_anomaly_mark(input_path: str, output_path: str, numeric_columns: Optional[str], z_threshold: float, diff_threshold: float):
    df = read_structured_data(input_path)
    cols = _select_numeric_columns(df, numeric_columns)

    if not cols:
        print("[WARN] 未选中任何数值列，数据将原样输出，且标记列为空。")
        df_out = df.copy()
        df_out["anomaly_flag"] = False
        df_out["anomaly_reasons"] = ""
    else:
        df_out = _mark_anomalies(df, cols, z_threshold, diff_threshold)

    write_structured_data(df_out, output_path)
    print(
        f"[OK] 时序异常标记完成 -> {output_path}\n"
        f"   数值列: {cols if cols else '无'}\n"
        f"   行数: {len(df_out)}"
    )


def main():
    parser = argparse.ArgumentParser(description="时序/数值异常标记：Z-Score + 差分突变检测")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument("--numeric_columns", required=False, default=None, help="需检测的数值列，逗号分隔；默认全部数值列")
    parser.add_argument("--z_threshold", type=float, default=3.0, help="Z-Score 阈值，默认 3.0")
    parser.add_argument("--diff_threshold", type=float, default=3.0, help="差分突变阈值(倍数标准差)，默认 3.0")

    args = parser.parse_args()
    time_anomaly_mark(
        input_path=args.input_path,
        output_path=args.output_path,
        numeric_columns=args.numeric_columns,
        z_threshold=args.z_threshold,
        diff_threshold=args.diff_threshold,
    )


if __name__ == "__main__":
    main()
