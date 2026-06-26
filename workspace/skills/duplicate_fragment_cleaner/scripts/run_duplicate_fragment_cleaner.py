import argparse
import json
import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple


FULLWIDTH_TRANSLATION = str.maketrans(
    {
        "，": ",",
        "。": ".",
        "！": "!",
        "？": "?",
        "：": ":",
        "；": ";",
        "（": "(",
        "）": ")",
        "【": "[",
        "】": "]",
        "「": '"',
        "」": '"',
        "『": '"',
        "』": '"',
        "《": "<",
        "》": ">",
        "〔": "[",
        "〕": "]",
        "｛": "{",
        "｝": "}",
        "　": " ",
        "、": ",",
    }
)
WHITESPACE_PATTERN = re.compile(r"\s+")
EXTRA_BLANK_LINES_PATTERN = re.compile(r"\n{3,}")


@dataclass
class LineItem:
    index: int
    text: str
    normalized: str
    length: int
    keep: bool = True


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """加载 JSONL 文件。"""
    if not os.path.exists(path):
        return []
    items: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                items.append({"_raw": line, "_parse_error": True})
    return items


def save_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    """保存 JSONL 文件。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_for_compare(text: str) -> str:
    normalized = text.translate(FULLWIDTH_TRANSLATION)
    normalized = WHITESPACE_PATTERN.sub(" ", normalized)
    return normalized.strip()


def is_candidate_line(text: str, min_fragment_length: int) -> bool:
    stripped = text.strip()
    return bool(stripped) and len(stripped) >= min_fragment_length


def similarity_score(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    shorter = min(len(left), len(right))
    longer = max(len(left), len(right))
    if longer == 0:
        return 0.0
    if shorter / longer < 0.75:
        return 0.0
    matcher = SequenceMatcher(None, left, right, autojunk=False)
    if matcher.quick_ratio() < 0.5:
        return 0.0
    return matcher.ratio()


class DuplicateFragmentCleaner:
    """文本内部重复片段模糊清理器。"""

    def __init__(self, text_field: str = "text", mark_cleaned: bool = True):
        self.text_field = text_field
        self.mark_cleaned = mark_cleaned

    def clean_text(
        self,
        text: str,
        min_fragment_length: int,
        max_fragment_length: int,
        similarity_threshold: float,
        keep_first: bool,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        lines = text.splitlines(keepends=True)
        if not lines:
            return text, []

        items: List[LineItem] = []
        for index, raw_line in enumerate(lines):
            if not is_candidate_line(raw_line, min_fragment_length):
                items.append(LineItem(index=index, text=raw_line, normalized="", length=len(raw_line)))
                continue
            if len(raw_line.strip()) > max_fragment_length:
                items.append(LineItem(index=index, text=raw_line, normalized="", length=len(raw_line)))
                continue
            normalized = normalize_for_compare(raw_line)
            items.append(LineItem(index=index, text=raw_line, normalized=normalized, length=len(raw_line)))

        kept: List[LineItem] = []
        removed_details: List[Dict[str, Any]] = []

        for item in items:
            if not item.normalized:
                kept.append(item)
                continue

            matched: Optional[Tuple[LineItem, float]] = None
            for kept_item in kept:
                if not kept_item.normalized:
                    continue
                score = similarity_score(item.normalized, kept_item.normalized)
                if score >= similarity_threshold:
                    matched = (kept_item, score)
                    break

            if matched is None:
                kept.append(item)
                continue

            matched_item, matched_score = matched
            if keep_first:
                item.keep = False
                removed_details.append(
                    {
                        "index": item.index,
                        "removed_text": item.text.rstrip("\r\n"),
                        "matched_text": matched_item.text.rstrip("\r\n"),
                        "similarity": round(matched_score, 4),
                    }
                )
            else:
                if matched_item.keep:
                    matched_item.keep = False
                    removed_details.append(
                        {
                            "index": matched_item.index,
                            "removed_text": matched_item.text.rstrip("\r\n"),
                            "matched_text": item.text.rstrip("\r\n"),
                            "similarity": round(matched_score, 4),
                        }
                    )
                kept.append(item)

        output_text = "".join(line.text for line in items if line.keep)
        output_text = EXTRA_BLANK_LINES_PATTERN.sub("\n\n", output_text)
        return output_text, removed_details

    def process(self, args: argparse.Namespace) -> Dict[str, Any]:
        data = load_jsonl(args.input)

        cleaned_count = 0
        total_fragments_removed = 0
        removed_samples: List[Dict[str, Any]] = []
        results: List[Dict[str, Any]] = []

        for item in data:
            if not isinstance(item, dict):
                results.append(item)
                continue

            text = item.get(args.text_field)
            if not isinstance(text, str) or not text:
                results.append(item)
                continue

            cleaned_text, removed_details = self.clean_text(
                text=text,
                min_fragment_length=args.min_fragment_length,
                max_fragment_length=args.max_fragment_length,
                similarity_threshold=args.similarity_threshold,
                keep_first=args.keep_first,
            )

            if not removed_details or cleaned_text == text:
                results.append(item)
                continue

            cleaned_count += 1
            total_fragments_removed += len(removed_details)
            removed_samples.append(
                {
                    "id": item.get("id"),
                    "removed_fragments": len(removed_details),
                    "original": text,
                    "cleaned": cleaned_text,
                    "details": removed_details[:20],
                }
            )

            new_item = item.copy()
            new_item[args.text_field] = cleaned_text
            if self.mark_cleaned:
                new_item["_fragment_cleaned"] = True
                new_item["_fragments_removed"] = len(removed_details)
            results.append(new_item)

        save_jsonl(args.output, results)

        if args.log_file and removed_samples:
            log_data = {
                "total_fragments_removed": total_fragments_removed,
                "unique_fragments": len(removed_samples),
                "samples": removed_samples[:100],
            }
            os.makedirs(os.path.dirname(args.log_file) or ".", exist_ok=True)
            with open(args.log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

        print("[OK] Duplicate fragment fuzzy cleaning completed")
        print(f"   Input: {args.input}")
        print(f"   Output: {args.output}")
        print(f"   Total samples: {len(data)}")
        print(f"   Samples cleaned: {cleaned_count}")
        print(f"   Fragments removed: {total_fragments_removed}")
        print(f"   Unique fragments: {len(removed_samples)}")

        return {
            "input": args.input,
            "output": args.output,
            "total_samples": len(data),
            "cleaned_samples": cleaned_count,
            "fragments_removed": total_fragments_removed,
            "unique_fragments": len(removed_samples),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Duplicate fragment cleaner - 文本内部重复片段模糊清理")
    parser.add_argument("--input", required=True, help="输入 JSONL 文件路径")
    parser.add_argument("--output", required=True, help="输出 JSONL 文件路径")
    parser.add_argument("--text_field", default="text", help="文本字段名，默认 text")
    parser.add_argument("--min_fragment_length", type=int, default=30, help="最小候选片段长度，默认 30")
    parser.add_argument("--max_fragment_length", type=int, default=500, help="最大候选片段长度，默认 500")
    parser.add_argument(
        "--similarity_threshold",
        type=float,
        default=0.88,
        help="模糊相似度阈值，默认 0.88",
    )
    parser.add_argument("--keep_first", type=str_to_bool, default=True, help="保留第一次出现，默认 True")
    parser.add_argument("--mark_cleaned", type=str_to_bool, default=True, help="标记已清洗样本，默认 True")
    parser.add_argument("--log_file", default="", help="删除片段日志文件路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cleaner = DuplicateFragmentCleaner(text_field=args.text_field, mark_cleaned=args.mark_cleaned)
    cleaner.process(args)


if __name__ == "__main__":
    main()
