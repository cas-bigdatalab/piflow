import argparse
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple


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


def parse_datetime(dt_str: str, fmt: str = None) -> datetime:
    if fmt:
        return datetime.strptime(dt_str, fmt)

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    ]
    for fmt_item in formats:
        try:
            return datetime.strptime(dt_str, fmt_item)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {dt_str}")


def parse_window_size(size_str: str) -> timedelta:
    if size_str.endswith("d"):
        return timedelta(days=int(size_str[:-1]))
    if size_str.endswith("h"):
        return timedelta(hours=int(size_str[:-1]))
    if size_str.endswith("m"):
        return timedelta(days=30 * int(size_str[:-1]))
    if size_str.endswith("w"):
        return timedelta(weeks=int(size_str[:-1]))
    raise ValueError(f"Unsupported window size: {size_str}")


def window_floor(dt: datetime, window_size: str, window_delta: timedelta) -> datetime:
    if window_size.endswith("d"):
        return datetime(dt.year, dt.month, dt.day)
    if window_size.endswith("h"):
        return datetime(dt.year, dt.month, dt.day, dt.hour)
    if window_size.endswith("m"):
        month_index = (dt.year * 12 + dt.month - 1) // int(window_size[:-1]) * int(window_size[:-1])
        year = month_index // 12
        month = month_index % 12 + 1
        return datetime(year, month, 1)
    if window_size.endswith("w"):
        start_of_day = datetime(dt.year, dt.month, dt.day)
        return start_of_day - timedelta(days=dt.weekday())

    base = datetime(1970, 1, 1)
    offset = int((dt - base).total_seconds() // window_delta.total_seconds())
    return base + timedelta(seconds=offset * window_delta.total_seconds())


def window_label(window_start: datetime, window_size: str) -> str:
    if window_size.endswith("d"):
        return window_start.strftime("%Y-%m-%d")
    if window_size.endswith("h"):
        return window_start.strftime("%Y-%m-%d_%H")
    if window_size.endswith("m"):
        return window_start.strftime("%Y-%m")
    if window_size.endswith("w"):
        return window_start.strftime("%Y-%m-%d")
    return window_start.isoformat()


def sample_by_window(
    records: List[Dict[str, Any]],
    time_field: str,
    window_size: str,
    time_format: str = None,
    sample_per_window: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    window_delta = parse_window_size(window_size)
    windows: Dict[str, List[Tuple[datetime, Dict[str, Any]]]] = {}

    for record in records:
        dt_str = record.get(time_field)
        if not dt_str:
            continue
        try:
            dt = parse_datetime(dt_str, time_format)
        except (ValueError, TypeError):
            continue

        start = window_floor(dt, window_size, window_delta)
        key = window_label(start, window_size)
        windows.setdefault(key, []).append((dt, record))

    sampled = []
    window_stats = {}
    for key, group in sorted(windows.items()):
        group.sort(key=lambda item: item[0])
        if sample_per_window >= len(group):
            selected = group
        elif sample_per_window == 1:
            selected = [group[0]]
        else:
            step = (len(group) - 1) / (sample_per_window - 1)
            selected_indices = []
            used = set()
            for i in range(sample_per_window):
                idx = round(i * step)
                while idx in used and idx < len(group) - 1:
                    idx += 1
                used.add(idx)
                selected_indices.append(idx)
            selected = [group[idx] for idx in selected_indices]

        for sample_index, (_, record) in enumerate(selected):
            sampled_record = record.copy()
            sampled_record["_time_window"] = key
            sampled_record["_window_sample_index"] = sample_index
            sampled.append(sampled_record)

        window_stats[key] = {
            "total": len(group),
            "sampled": len(selected),
        }

    return sampled, window_stats


def main():
    parser = argparse.ArgumentParser(description="Time window sampler - 时间窗口采样算子")
    parser.add_argument("--input", required=True, help="输入JSONL文件")
    parser.add_argument("--output", required=True, help="输出JSONL文件")
    parser.add_argument("--time_field", required=True, help="时间字段名")
    parser.add_argument("--window_size", required=True, help="窗口大小（如1d=1天, 2h=2小时, 1m=1月, 1w=1周）")
    parser.add_argument("--time_format", default=None, help="时间格式（如%%Y-%%m-%%d %%H:%%M:%%S）")
    parser.add_argument("--sample_per_window", type=int, default=1, help="每个窗口采样数量（默认1）")
    parser.add_argument("--log_file", default="", help="日志文件路径")

    args = parser.parse_args()

    records = load_jsonl(args.input)
    sampled, stats = sample_by_window(
        records,
        args.time_field,
        args.window_size,
        args.time_format,
        args.sample_per_window,
    )

    save_jsonl(args.output, sampled)

    print(f"[OK] Time window sampling completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total records: {len(records)}")
    print(f"   Time field: {args.time_field}")
    print(f"   Window size: {args.window_size}")
    print(f"   Windows: {len(stats)}")
    print(f"   Sampled records: {len(sampled)}")

    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
        with open(args.log_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "operation": "time_window_sample",
                    "time_field": args.time_field,
                    "window_size": args.window_size,
                    "total_records": len(records),
                    "sampled_records": len(sampled),
                    "window_count": len(stats),
                    "window_stats": stats,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"   Log saved to: {args.log_file}")


if __name__ == "__main__":
    main()
