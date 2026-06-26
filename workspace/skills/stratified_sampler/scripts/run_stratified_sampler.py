import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402


def _format_group_key(key: Any) -> str:
    if isinstance(key, tuple):
        return " | ".join(str(item) for item in key)
    return str(key)


def _sample_group(df: pd.DataFrame, count: int, seed: int) -> pd.DataFrame:
    if count <= 0 or df.empty:
        return df.iloc[0:0].copy()
    if count >= len(df):
        return df.copy()
    return df.sample(n=count, replace=False, random_state=seed)


def _sample_ratio_mode(frame: pd.DataFrame, strata_fields: List[str], ratio: float, min_samples: int, seed: int) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    groups = list(frame.groupby(strata_fields, dropna=False, sort=False))
    sampled_frames = []
    stats: Dict[str, Dict[str, int]] = {}
    for index, (key, group) in enumerate(groups):
        target = math.ceil(len(group) * ratio)
        if min_samples > 0:
            target = max(target, min_samples)
        target = min(target, len(group))
        sampled_group = _sample_group(group, target, seed + index)
        sampled_frames.append(sampled_group)
        stats[_format_group_key(key)] = {"total": len(group), "sampled": len(sampled_group)}
    sampled = pd.concat(sampled_frames, ignore_index=True) if sampled_frames else frame.iloc[0:0].copy()
    sampled = sampled.sample(frac=1, random_state=seed).reset_index(drop=True) if len(sampled) > 1 else sampled.reset_index(drop=True)
    return sampled, stats


def _sample_num_mode(frame: pd.DataFrame, strata_fields: List[str], sample_num: int, seed: int) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    groups = list(frame.groupby(strata_fields, dropna=False, sort=False))
    sampled_frames = []
    stats: Dict[str, Dict[str, int]] = {}
    for index, (key, group) in enumerate(groups):
        target = min(sample_num, len(group))
        sampled_group = _sample_group(group, target, seed + index)
        sampled_frames.append(sampled_group)
        stats[_format_group_key(key)] = {"total": len(group), "sampled": len(sampled_group)}
    sampled = pd.concat(sampled_frames, ignore_index=True) if sampled_frames else frame.iloc[0:0].copy()
    sampled = sampled.sample(frac=1, random_state=seed).reset_index(drop=True) if len(sampled) > 1 else sampled.reset_index(drop=True)
    return sampled, stats


def _sample_size_mode(frame: pd.DataFrame, strata_fields: List[str], sample_size: int, min_samples: int, seed: int) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    groups = list(frame.groupby(strata_fields, dropna=False, sort=False))
    total = len(frame)
    allocations: List[int] = []
    remainders: List[Tuple[float, int]] = []
    stats: Dict[str, Dict[str, int]] = {}

    if sample_size > total:
        sample_size = total

    for index, (key, group) in enumerate(groups):
        exact = sample_size * len(group) / total if total else 0
        target = math.floor(exact)
        if min_samples > 0 and len(group) > 0:
            target = max(target, min_samples)
        target = min(target, len(group))
        allocations.append(target)
        remainders.append((exact - math.floor(exact), index))
        stats[_format_group_key(key)] = {"total": len(group), "sampled": target}

    current = sum(allocations)
    if current > sample_size:
        over = current - sample_size
        for _, index in sorted(remainders):
            if over <= 0:
                break
            removable = min(over, allocations[index])
            allocations[index] -= removable
            stats[_format_group_key(groups[index][0])]["sampled"] = allocations[index]
            over -= removable
    elif current < sample_size:
        need = sample_size - current
        for _, index in sorted(remainders, reverse=True):
            if need <= 0:
                break
            group_size = len(groups[index][1])
            available = group_size - allocations[index]
            if available <= 0:
                continue
            add = min(available, need)
            allocations[index] += add
            stats[_format_group_key(groups[index][0])]["sampled"] = allocations[index]
            need -= add

    sampled_frames = []
    for index, (_, group) in enumerate(groups):
        sampled_group = _sample_group(group, allocations[index], seed + index)
        sampled_frames.append(sampled_group)
    sampled = pd.concat(sampled_frames, ignore_index=True) if sampled_frames else frame.iloc[0:0].copy()
    sampled = sampled.sample(frac=1, random_state=seed).reset_index(drop=True) if len(sampled) > 1 else sampled.reset_index(drop=True)
    return sampled, stats


def process(input_path: str, output_path: str, strata_field: str, sample_size: Optional[int] = None,
            sample_ratio: Optional[float] = None, sample_num: Optional[int] = None,
            min_samples: int = 0, seed: int = 42, log_file: str = "") -> Dict[str, Any]:
    if sum(value is not None for value in [sample_size, sample_ratio, sample_num]) != 1:
        raise ValueError("Exactly one of sample_size, sample_ratio, sample_num must be provided")

    if min_samples < 0:
        raise ValueError("min_samples must be non-negative")

    frame = read_structured_data(input_path)
    if frame.empty:
        raise ValueError("Input data is empty")

    strata_fields = [field.strip() for field in strata_field.split(",") if field.strip()]
    if not strata_fields:
        raise ValueError("strata_field cannot be empty")

    missing = [field for field in strata_fields if field not in frame.columns]
    if missing:
        raise ValueError(f"Missing strata field(s): {', '.join(missing)}")

    if sample_size is not None:
        sampled, stats = _sample_size_mode(frame, strata_fields, int(sample_size), int(min_samples), int(seed))
        mode = "sample_size"
    elif sample_ratio is not None:
        ratio = float(sample_ratio)
        if not 0 < ratio <= 1:
            raise ValueError("sample_ratio must be within (0, 1]")
        sampled, stats = _sample_ratio_mode(frame, strata_fields, ratio, int(min_samples), int(seed))
        mode = "sample_ratio"
    else:
        num = int(sample_num)
        if num <= 0:
            raise ValueError("sample_num must be positive")
        if min_samples > 0:
            raise ValueError("min_samples cannot be combined with sample_num")
        sampled, stats = _sample_num_mode(frame, strata_fields, num, int(seed))
        mode = "sample_num"

    write_structured_data(sampled, output_path)

    log = {
        "operation": "stratified_sample",
        "mode": mode,
        "input_path": input_path,
        "output_path": output_path,
        "strata_field": strata_field,
        "total_records": len(frame),
        "sampled_records": len(sampled),
        "strata_stats": stats,
        "seed": int(seed),
    }

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    print("[OK] Stratified sampling completed")
    print(f"   Input: {input_path}")
    print(f"   Output: {output_path}")
    print(f"   Total records: {len(frame)}")
    print(f"   Strata field: {strata_field}")
    print(f"   Sampled records: {len(sampled)}")
    print("   Strata distribution:")
    for key, s in stats.items():
        if s["total"] > 0:
            print(f"      {key}: {s['sampled']}/{s['total']} ({s['sampled']/s['total']:.1%})")
        else:
            print(f"      {key}: 0/0")
    if log_file:
        print(f"   Log saved to: {log_file}")

    return log


def main() -> None:
    parser = argparse.ArgumentParser(description="Stratified sampler - 分层采样算子")
    parser.add_argument("--input", required=True, help="输入结构化数据文件")
    parser.add_argument("--output", required=True, help="输出结构化数据文件")
    parser.add_argument("--strata_field", required=True, help="分层字段（如category, label等）")
    parser.add_argument("--sample_size", type=int, default=None, help="总采样数量")
    parser.add_argument("--sample_ratio", type=float, default=None, help="分层采样比例")
    parser.add_argument("--sample_num", type=int, default=None, help="每层固定采样数量")
    parser.add_argument("--min_samples", type=int, default=0, help="每层最小采样数量")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--log_file", default="", help="日志文件路径")

    args = parser.parse_args()
    process(
        input_path=args.input,
        output_path=args.output,
        strata_field=args.strata_field,
        sample_size=args.sample_size,
        sample_ratio=args.sample_ratio,
        sample_num=args.sample_num,
        min_samples=args.min_samples,
        seed=args.seed,
        log_file=args.log_file,
    )


if __name__ == "__main__":
    main()
