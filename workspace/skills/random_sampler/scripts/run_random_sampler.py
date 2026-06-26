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


def sample_by_count(records: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    random.seed(seed)
    if count >= len(records):
        return records
    return random.sample(records, count)


def sample_by_ratio(records: List[Dict[str, Any]], ratio: float, seed: int) -> List[Dict[str, Any]]:
    count = int(len(records) * ratio)
    return sample_by_count(records, count, seed)


def main():
    parser = argparse.ArgumentParser(description="Random sampler - 随机采样算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--output", required=True, help="输出JSONL文件")
    parser.add_argument("--method", choices=["count", "ratio"], required=True,
                       help="采样方式：按数量或比例")
    parser.add_argument("--count", type=int, default=0, help="采样数量（method=count时）")
    parser.add_argument("--ratio", type=float, default=0.0, help="采样比例0-1（method=ratio时）")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--log_file", default="", help="日志文件路径")
    
    args = parser.parse_args()
    
    records = load_jsonl(args.input)
    total = len(records)
    
    if args.method == "count":
        sampled = sample_by_count(records, args.count, args.seed)
    else:
        sampled = sample_by_ratio(records, args.ratio, args.seed)
    
    save_jsonl(args.output, sampled)
    
    print(f"[OK] Random sampling completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total records: {total}")
    print(f"   Sampled records: {len(sampled)}")
    print(f"   Sampling rate: {len(sampled)/total:.2%}" if total > 0 else "   Sampling rate: N/A")
    print(f"   Random seed: {args.seed}")
    
    if args.log_file:
        log = {
            "operation": "random_sample",
            "method": args.method,
            "total_records": total,
            "sampled_records": len(sampled),
            "seed": args.seed
        }
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
