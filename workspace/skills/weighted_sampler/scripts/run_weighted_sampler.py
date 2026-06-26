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
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_bool(value: str) -> bool:
    return str(value).lower() == "true"


def weighted_sample(
    records: List[Dict[str, Any]],
    weight_field: str,
    sample_size: int,
    seed: int,
    with_replacement: bool = False,
) -> List[Dict[str, Any]]:
    random.seed(seed)

    weighted_records = []
    for record in records:
        raw_weight = record.get(weight_field, 0)
        try:
            weight = float(raw_weight)
        except (ValueError, TypeError):
            continue
        if weight > 0:
            weighted_records.append((record, weight))

    if not weighted_records:
        return []

    if with_replacement:
        weights = [weight for _, weight in weighted_records]
        total_weight = sum(weights)
        if total_weight <= 0:
            return []

        normalized_weights = [weight / total_weight for weight in weights]
        sampled_indices = random.choices(
            range(len(weighted_records)),
            weights=normalized_weights,
            k=sample_size,
        )
        sampled = []
        for index in sampled_indices:
            record, weight = weighted_records[index]
            sampled_record = record.copy()
            sampled_record["_sample_weight"] = weight
            sampled_record["_sample_normalized_weight"] = normalized_weights[index]
            sampled.append(sampled_record)
        return sampled

    if sample_size >= len(weighted_records):
        total_weight = sum(weight for _, weight in weighted_records)
        sampled = []
        for record, weight in weighted_records:
            sampled_record = record.copy()
            sampled_record["_sample_weight"] = weight
            sampled_record["_sample_normalized_weight"] = weight / total_weight
            sampled.append(sampled_record)
        return sampled

    pool = weighted_records.copy()
    sampled_pairs = []
    for _ in range(sample_size):
        total_weight = sum(weight for _, weight in pool)
        if total_weight <= 0:
            break

        threshold = random.random() * total_weight
        cumulative = 0.0
        chosen_index = len(pool) - 1
        for index, (record, weight) in enumerate(pool):
            cumulative += weight
            if threshold <= cumulative:
                chosen_index = index
                break

        sampled_pairs.append(pool.pop(chosen_index))

    total_sampled_weight = sum(weight for _, weight in sampled_pairs)
    sampled = []
    for record, weight in sampled_pairs:
        sampled_record = record.copy()
        sampled_record["_sample_weight"] = weight
        sampled_record["_sample_normalized_weight"] = weight / total_sampled_weight
        sampled.append(sampled_record)
    return sampled


def main() -> None:
    parser = argparse.ArgumentParser(description="Weighted sampler - 加权采样算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--output", required=True, help="输出JSONL文件")
    parser.add_argument("--weight_field", required=True, help="权重字段名")
    parser.add_argument("--sample_size", type=int, required=True, help="采样数量")
    parser.add_argument("--with_replacement", type=parse_bool, default=False, help="有放回采样（默认无放回）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--log_file", default="", help="日志文件路径")

    args = parser.parse_args()

    records = load_jsonl(args.input)
    sampled = weighted_sample(
        records=records,
        weight_field=args.weight_field,
        sample_size=args.sample_size,
        seed=args.seed,
        with_replacement=args.with_replacement,
    )

    save_jsonl(args.output, sampled)

    print("[OK] Weighted sampling completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total records: {len(records)}")
    print(f"   Weight field: {args.weight_field}")
    print(f"   Sampled records: {len(sampled)}")
    print(f"   With replacement: {args.with_replacement}")
    print(f"   Random seed: {args.seed}")

    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "operation": "weighted_sample",
                    "weight_field": args.weight_field,
                    "total_records": len(records),
                    "sampled_records": len(sampled),
                    "with_replacement": args.with_replacement,
                    "seed": args.seed,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
