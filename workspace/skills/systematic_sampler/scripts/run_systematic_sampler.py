import argparse
import json
import os
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


def systematic_sample(records: List[Dict[str, Any]], interval: int, 
                     start_offset: int = 0) -> List[Dict[str, Any]]:
    """等间隔系统采样"""
    sampled = []
    for i in range(start_offset, len(records), interval):
        record = records[i]
        record["_sample_index"] = i
        record["_sample_interval"] = interval
        sampled.append(record)
    return sampled


def main():
    parser = argparse.ArgumentParser(description="Systematic sampler - 系统采样算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--output", required=True, help="输出JSONL文件")
    parser.add_argument("--method", choices=["interval", "count"], required=True,
                       help="采样方式：interval（按间隔）或count（按数量计算间隔）")
    parser.add_argument("--interval", type=int, default=0, help="采样间隔（method=interval时）")
    parser.add_argument("--count", type=int, default=0, help="目标采样数量（method=count时自动计算间隔）")
    parser.add_argument("--start_offset", type=int, default=0, help="起始偏移量（默认0）")
    parser.add_argument("--log_file", default="", help="日志文件路径")
    
    args = parser.parse_args()
    
    records = load_jsonl(args.input)
    total = len(records)
    
    if args.method == "interval":
        interval = args.interval if args.interval > 0 else 1
    else:
        # 根据目标数量计算间隔
        if args.count > 0 and args.count < total:
            interval = max(1, total // args.count)
        else:
            interval = 1

    sampled = systematic_sample(records, interval, args.start_offset)
    if args.method == "count" and args.count > 0 and len(sampled) > args.count:
        sampled = sampled[:args.count]

    save_jsonl(args.output, sampled)
    
    print(f"[OK] Systematic sampling completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total records: {total}")
    print(f"   Sampling interval: {interval}")
    print(f"   Start offset: {args.start_offset}")
    print(f"   Sampled records: {len(sampled)}")
    print(f"   Sampling rate: {len(sampled)/total:.2%}" if total > 0 else "   Sampling rate: N/A")
    
    if args.log_file:
        log = {
            "operation": "systematic_sample",
            "method": args.method,
            "interval": interval,
            "start_offset": args.start_offset,
            "total_records": total,
            "sampled_records": len(sampled)
        }
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
