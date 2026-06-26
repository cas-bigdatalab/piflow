import argparse
import json
import math
import os
from typing import Any, Dict, List, Optional


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


def z_score_normalize(values: List[float]) -> List[float]:
    if not values:
        return values
    mean = sum(values) / len(values)
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
    if std == 0:
        return [0.0] * len(values)
    return [(x - mean) / std for x in values]


def min_max_normalize(values: List[float], new_min: float = 0, new_max: float = 1) -> List[float]:
    if not values:
        return values
    old_min, old_max = min(values), max(values)
    if old_max == old_min:
        return [new_min] * len(values)
    return [new_min + (x - old_min) * (new_max - new_min) / (old_max - old_min) for x in values]


def apply_normalization(records: List[Dict[str, Any]], field: str,
                        method: str, params: Dict[str, Any]) -> tuple:
    values = []
    indices = []
    for i, r in enumerate(records):
        if field in r and r[field] is not None:
            try:
                values.append(float(r[field]))
                indices.append(i)
            except (ValueError, TypeError):
                pass

    if not values:
        return records, 0

    if method == "z_score":
        normalized = z_score_normalize(values)
    elif method == "min_max":
        normalized = min_max_normalize(values, params.get("new_min", 0), params.get("new_max", 1))
    else:
        return records, 0

    changed = 0
    for idx, norm_val in zip(indices, normalized):
        old_val = records[idx][field]
        records[idx][field] = norm_val
        if old_val != norm_val:
            changed += 1
        records[idx][f"_{field}_normalized"] = True
        records[idx][f"_{field}_original"] = old_val

    return records, changed


def main():
    parser = argparse.ArgumentParser(description="Data normalizer - 数据标准化算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--output", required=True, help="输出JSONL文件")
    parser.add_argument("--field", required=True, help="要标准化的字段")
    parser.add_argument("--method", required=True,
                        choices=["z_score", "min_max"],
                        help="标准化方法")
    parser.add_argument("--new_min", type=float, default=0, help="min_max目标最小值")
    parser.add_argument("--new_max", type=float, default=1, help="min_max目标最大值")
    parser.add_argument("--log_file", default="", help="日志文件路径")

    args = parser.parse_args()

    records = load_jsonl(args.input)
    total = len(records)

    params = {}
    if args.method == "min_max":
        params = {"new_min": args.new_min, "new_max": args.new_max}

    records, changed = apply_normalization(records, args.field, args.method, params)

    save_jsonl(args.output, records)

    print(f"[OK] Data normalization completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total records: {total}")
    print(f"   Field '{args.field}' normalized with method: {args.method}")
    print(f"   Records changed: {changed}")

    if args.log_file:
        log = {
            "operation": "normalization",
            "field": args.field,
            "method": args.method,
            "total_records": total,
            "changed": changed,
            "params": params
        }
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
