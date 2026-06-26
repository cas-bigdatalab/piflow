import argparse
import json
import os
import random
from typing import Any, Dict, List


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def allocate_counts(total: int, ratios: List[float]) -> List[int]:
    if total <= 0:
        return [0 for _ in ratios]

    total_ratio = sum(ratios)
    if total_ratio <= 0:
        raise ValueError("分割比例总和必须大于0")

    normalized = [r / total_ratio for r in ratios]
    raw_counts = [total * ratio for ratio in normalized]
    counts = [int(count) for count in raw_counts]
    remainder = total - sum(counts)

    if remainder > 0:
        ranked = sorted(
            range(len(ratios)),
            key=lambda i: (
                raw_counts[i] - counts[i],
                normalized[i],
                -i,
            ),
            reverse=True,
        )
        for idx in ranked[:remainder]:
            counts[idx] += 1

    return counts


def stratified_split(records: List[Dict[str, Any]], split_ratios: List[float],
                    stratify_field: str = None, seed: int = 42) -> List[List[Dict[str, Any]]]:
    """按比例分割数据，支持分层分割"""
    random.seed(seed)

    if stratify_field:
        strata = {}
        for r in records:
            key = r.get(stratify_field, "__unknown__")
            if key not in strata:
                strata[key] = []
            strata[key].append(r)

        splits = [[] for _ in split_ratios]
        for group in strata.values():
            random.shuffle(group)
            counts = allocate_counts(len(group), split_ratios)
            start = 0
            for i, count in enumerate(counts):
                end = start + count
                splits[i].extend(group[start:end])
                start = end

        for s in splits:
            random.shuffle(s)

        return splits

    records = records.copy()
    random.shuffle(records)
    counts = allocate_counts(len(records), split_ratios)

    splits = []
    start = 0
    for count in counts:
        end = start + count
        splits.append(records[start:end])
        start = end

    return splits


def main():
    parser = argparse.ArgumentParser(description="Data splitter - 数据分割算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--outputs", required=True,
                       help="输出文件路径，逗号分隔（如train.jsonl,valid.jsonl,test.jsonl）")
    parser.add_argument("--ratios", required=True,
                       help="分割比例，逗号分隔（如0.7,0.2,0.1，总和应等于1）")
    parser.add_argument("--stratify_field", default="",
                       help="分层字段（用于分层分割，保持类别分布）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--log_file", default="", help="日志文件路径")

    args = parser.parse_args()

    output_paths = [p.strip() for p in args.outputs.split(",")]
    ratios = [float(r.strip()) for r in args.ratios.split(",")]

    if len(output_paths) != len(ratios):
        raise ValueError("输出文件数量和分割比例数量必须相同")

    if abs(sum(ratios) - 1.0) > 0.001:
        print(f"[WARN] 比例总和为{sum(ratios)}，建议调整为1.0")

    records = load_jsonl(args.input)
    total = len(records)

    stratify = args.stratify_field if args.stratify_field else None
    splits = stratified_split(records, ratios, stratify, args.seed)

    for path, split in zip(output_paths, splits):
        save_jsonl(path, split)
        print(f"   [{path}] {len(split)} records ({len(split)/total:.1%})")

    print(f"[OK] Data splitting completed")
    print(f"   Input: {args.input}")
    print(f"   Total records: {total}")
    print(f"   Split ratios: {ratios}")
    print(f"   Stratified: {stratify is not None}")
    if stratify:
        print(f"   Stratify field: {args.stratify_field}")
    print(f"   Random seed: {args.seed}")

    if args.log_file:
        log = {
            "operation": "data_split",
            "total_records": total,
            "ratios": ratios,
            "stratified": stratify is not None,
            "stratify_field": args.stratify_field if stratify else None,
            "seed": args.seed,
            "splits": [
                {"output": path, "count": len(split), "ratio": len(split) / total if total else 0}
                for path, split in zip(output_paths, splits)
            ]
        }
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
