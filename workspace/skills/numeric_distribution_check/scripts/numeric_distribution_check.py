import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

STAT_FUNCS = {
    "mean": lambda s: s.mean(),
    "median": lambda s: s.median(),
    "std": lambda s: s.std(),
    "min": lambda s: s.min(),
    "max": lambda s: s.max(),
    "p25": lambda s: s.quantile(0.25),
    "p75": lambda s: s.quantile(0.75),
}


def _parse_stat_constraints(raw: str) -> List[Tuple[str, float, float]]:
    result: List[Tuple[str, float, float]] = []
    for chunk in raw.replace(";", " ").split():
        parts = [part.strip() for part in chunk.split(",") if part.strip() != ""]
        if len(parts) != 3:
            raise ValueError(f"统计约束格式错误: {chunk}")
        stat, lo_raw, hi_raw = parts
        if stat not in STAT_FUNCS:
            raise ValueError(f"不支持的统计量: {stat}")
        lo = float(lo_raw)
        hi = float(hi_raw)
        if lo > hi:
            raise ValueError(f"统计约束下限大于上限: {chunk}")
        result.append((stat, lo, hi))
    if not result:
        raise ValueError("未解析到任何有效统计约束")
    return result


def _init_mark(df: pd.DataFrame, mark_field_name: str) -> tuple[str, str]:
    mark_field = mark_field_name or "QC0000"
    reason_field = f"{mark_field}_REASON"
    df[mark_field] = ""
    df[reason_field] = ""
    return mark_field, reason_field


def _apply_mark(df: pd.DataFrame, mask: pd.Series, mark_field: str, reason_field: str, qc_mark: str, reason: str) -> None:
    if mask.any():
        df.loc[mask, mark_field] = qc_mark
        df.loc[mask, reason_field] = reason


def _run_numeric(df: pd.DataFrame, value_field: str, stat_constraints: str, qc_mark: str, mark_field: str, reason_field: str) -> None:
    if value_field not in df.columns:
        print(f"[ERROR] 字段 '{value_field}' 不存在")
        sys.exit(1)

    vals = pd.to_numeric(df[value_field], errors="coerce").dropna()
    if len(vals) == 0:
        print("[WARN] 无数值数据")
        _apply_mark(df, pd.Series(True, index=df.index), mark_field, reason_field, qc_mark, "无数值数据")
        return

    try:
        constraints = _parse_stat_constraints(stat_constraints)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    issues = []
    invalid = False

    for stat, lo, hi in constraints:
        actual = STAT_FUNCS[stat](vals)
        detail = f"[{stat}] 期望 [{lo}, {hi}], 实际 {actual:.4f}"
        if actual < lo or actual > hi:
            issues.append((stat, f"{detail} ✗ 超限"))
            invalid = True
        else:
            print(f"  {detail} ✓")

    if invalid:
        _apply_mark(df, pd.Series(True, index=df.index), mark_field, reason_field, qc_mark, "数值分布超限")
        print(f"[QC FAIL] 数值分布校验未通过 ({len(issues)} 项):")
        for _, item in issues:
            print(f"  {item}")
    else:
        print(f"[QC PASS] 数值分布校验通过")


def _run_categorical(df: pd.DataFrame, category_field: str, max_categories: int, max_single_ratio: float, qc_mark: str, mark_field: str, reason_field: str) -> None:
    if category_field not in df.columns:
        print(f"[ERROR] 字段 '{category_field}' 不存在")
        sys.exit(1)

    category_series = df[category_field]
    normalized = category_series.astype(str).str.strip()
    valid_mask = category_series.notna() & normalized.ne("")
    valid_categories = normalized[valid_mask]

    if len(valid_categories) == 0:
        print("[ERROR] 分类字段没有有效取值")
        _apply_mark(df, pd.Series(True, index=df.index), mark_field, reason_field, qc_mark, "分类字段无有效取值")
        print("[QC FAIL] 分类频率校验未通过 (无有效分类数据)")
        return

    counts = valid_categories.value_counts()
    total = len(df)
    issues = []
    invalid_mask = pd.Series(False, index=df.index)
    reason_masks = []

    n_cats = len(counts)
    if max_categories and n_cats > max_categories:
        issues.append(f"[类别数] 实际 {n_cats} > 最大 {max_categories}")
        invalid_mask[:] = True
        reason_masks.append((pd.Series(True, index=df.index), "类别数超限"))

    if max_single_ratio:
        for cat, cnt in counts.items():
            ratio = cnt / len(valid_categories)
            if ratio > max_single_ratio:
                issues.append(f"[倾斜] 类别 '{cat[:30]}' 占比 {ratio:.1%} > {max_single_ratio:.0%}")
                cat_mask = valid_mask & (normalized == cat)
                invalid_mask |= cat_mask
                reason_masks.append((cat_mask, f"类别倾斜:{cat}"))

    print(f"[INFO] 总行数: {total}, 类别数: {n_cats}")
    for cat, cnt in counts.head(5).items():
        print(f"  {cat[:40]:40s} {cnt:5d} ({cnt / len(valid_categories):.1%})")
    if n_cats > 5:
        print(f"  ... 还有 {n_cats - 5} 个类别")

    if invalid_mask.any():
        _apply_mark(df, invalid_mask, mark_field, reason_field, qc_mark, "分类频率异常")
        for mask, reason in reason_masks:
            _apply_mark(df, mask, mark_field, reason_field, qc_mark, reason)
        print(f"[QC FAIL] 分类频率校验未通过 ({len(issues)} 项):")
        for item in issues:
            print(f"  {item}")
    else:
        print(f"[QC PASS] 分类频率校验通过")


def run(input_path, output_path, mode, value_field, stat_constraints, category_field, max_categories, max_single_ratio, qc_mark, mark_field_name):
    df = read_structured_data(input_path)
    mark_field, reason_field = _init_mark(df, mark_field_name)

    if mode == "numeric":
        _run_numeric(df, value_field, stat_constraints, qc_mark, mark_field, reason_field)
    elif mode == "categorical":
        _run_categorical(df, category_field, max_categories, max_single_ratio, qc_mark, mark_field, reason_field)
    else:
        print(f"[ERROR] 不支持的模式: {mode}")
        sys.exit(1)

    write_structured_data(df, output_path)
    print(f"[OK] 结果已写入 -> {output_path}")


def main():
    p = argparse.ArgumentParser(description="字段分布校验")
    p.add_argument("--input_path", required=True)
    p.add_argument("--output_path", required=True)
    p.add_argument("--mode", default="numeric", choices=["numeric", "categorical"])
    p.add_argument("--value_field", default="")
    p.add_argument("--stat_constraints", default="")
    p.add_argument("--category_field", default="")
    p.add_argument("--max_categories", type=int, default=0)
    p.add_argument("--max_single_ratio", type=float, default=0.0)
    p.add_argument("--qc_mark", required=True)
    p.add_argument("--mark_field_name", default="QC0000")
    args = p.parse_args()
    run(
        args.input_path,
        args.output_path,
        args.mode,
        args.value_field,
        args.stat_constraints,
        args.category_field,
        args.max_categories,
        args.max_single_ratio,
        args.qc_mark,
        args.mark_field_name,
    )


if __name__ == "__main__":
    main()
