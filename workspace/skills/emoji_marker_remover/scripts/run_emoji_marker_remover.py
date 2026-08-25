import argparse
import csv
import json
import unicodedata
from pathlib import Path
from typing import Any


VARIATION_SELECTORS = {"︎", "️"}
KEYCAP = "⃣"
ZWJ = "‍"
TAG_RANGE = range(0xE0020, 0xE0080)
REGIONAL_INDICATOR_RANGE = range(0x1F1E6, 0x1F200)
EMOJI_MODIFIER_RANGE = range(0x1F3FB, 0x1F400)
EMOJI_RANGES = (
    range(0x1F000, 0x1FB00),
    range(0x2300, 0x2400),
    range(0x2600, 0x2800),
    range(0x2B00, 0x2C00),
)
DEFAULT_EMOJI_RANGES = (
    range(0x1F000, 0x1FB00),
    range(0x231A, 0x231C),
    range(0x23E9, 0x23ED),
    range(0x23F0, 0x23F1),
    range(0x23F3, 0x23F4),
    range(0x25FD, 0x25FF),
    range(0x2614, 0x2616),
    range(0x2648, 0x2654),
    range(0x26AA, 0x26AC),
    range(0x26BD, 0x26BF),
    range(0x26C4, 0x26C6),
    range(0x26F2, 0x26F4),
    range(0x270A, 0x270C),
    range(0x2753, 0x2756),
    range(0x2795, 0x2798),
)
DEFAULT_EMOJI_CODEPOINTS = {
    0x267F, 0x2693, 0x26A1, 0x26CE, 0x26D4, 0x26EA, 0x26F5, 0x26FA, 0x26FD,
    0x2705, 0x2728, 0x274C, 0x274E, 0x2757, 0x27B0, 0x27BF, 0x2B1B, 0x2B1C,
    0x2B50, 0x2B55,
}
ORNAMENT_NAME_MARKERS = ("ORNAMENT", "DINGBAT", "HEART", "SPARKLE")


def _in_ranges(codepoint: int, ranges: tuple[range, ...]) -> bool:
    return any(codepoint in codepoint_range for codepoint_range in ranges)


def _is_emoji_candidate(character: str) -> bool:
    return _in_ranges(ord(character), EMOJI_RANGES)


def _is_default_emoji(character: str) -> bool:
    codepoint = ord(character)
    if codepoint in DEFAULT_EMOJI_CODEPOINTS or _in_ranges(codepoint, DEFAULT_EMOJI_RANGES):
        return True
    name = unicodedata.name(character, "")
    return any(marker in name for marker in ORNAMENT_NAME_MARKERS)


def remove_emoji_markers(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    cleaned: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        codepoint = ord(character)

        if character in "#*0123456789":
            sequence_end = index + 1
            if sequence_end < len(value) and value[sequence_end] in VARIATION_SELECTORS:
                sequence_end += 1
            if sequence_end < len(value) and value[sequence_end] == KEYCAP:
                index = sequence_end + 1
                continue

        if codepoint in REGIONAL_INDICATOR_RANGE:
            index += 1
            if index < len(value) and ord(value[index]) in REGIONAL_INDICATOR_RANGE:
                index += 1
            continue

        has_emoji_selector = index + 1 < len(value) and value[index + 1] == "️"
        if _is_default_emoji(character) or has_emoji_selector:
            index += 1
            while index < len(value):
                next_codepoint = ord(value[index])
                if value[index] in VARIATION_SELECTORS or next_codepoint in EMOJI_MODIFIER_RANGE or next_codepoint in TAG_RANGE:
                    index += 1
                    continue
                if value[index] == ZWJ:
                    joined_index = index + 1
                    if joined_index < len(value) and (
                        _is_emoji_candidate(value[joined_index])
                        or _is_default_emoji(value[joined_index])
                    ):
                        index = joined_index + 1
                        continue
                    index += 1
                    break
                break
            continue

        if character in VARIATION_SELECTORS or character == ZWJ or character == KEYCAP or codepoint in TAG_RANGE:
            index += 1
            continue

        cleaned.append(character)
        index += 1

    return "".join(cleaned)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="移除文本中的表情标识和装饰图标")
    parser.add_argument("--input_path", required=True, help="输入文本或数据文件路径")
    parser.add_argument("--output_path", required=True, help="清理结果文件路径")
    parser.add_argument(
        "--text_columns",
        default="",
        help="CSV 或 TSV 中待处理的文本列，逗号分隔；不填时处理全部列",
    )
    parser.add_argument(
        "--text_field",
        default="text",
        help="JSON 或 JSONL 中待处理的文本字段名",
    )
    return parser.parse_args()


def clean_json_value(value: Any, text_field: str) -> Any:
    if isinstance(value, str):
        return remove_emoji_markers(value)
    if isinstance(value, list):
        return [clean_json_value(item, text_field) for item in value]
    if isinstance(value, dict):
        cleaned = dict(value)
        if text_field in cleaned:
            cleaned[text_field] = remove_emoji_markers(cleaned[text_field])
        for key, item in cleaned.items():
            if key != text_field and isinstance(item, (dict, list)):
                cleaned[key] = clean_json_value(item, text_field)
        return cleaned
    return value


def clean_delimited_file(input_path: Path, output_path: Path, text_columns: str) -> None:
    delimiter = "\t" if input_path.suffix.lower() == ".tsv" else ","
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter=delimiter)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("输入文件缺少表头")
        selected_columns = [item.strip() for item in text_columns.split(",") if item.strip()]
        if not selected_columns:
            selected_columns = fieldnames
        missing_columns = sorted(set(selected_columns) - set(fieldnames))
        if missing_columns:
            raise ValueError(f"输入文件不存在文本列: {', '.join(missing_columns)}")
        with output_path.open("w", encoding="utf-8", newline="") as destination:
            writer = csv.DictWriter(destination, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            for row in reader:
                for column in selected_columns:
                    row[column] = remove_emoji_markers(row.get(column))
                writer.writerow(row)


def clean_json_file(input_path: Path, output_path: Path, text_field: str) -> None:
    with input_path.open("r", encoding="utf-8") as source:
        content = json.load(source)
    cleaned = clean_json_value(content, text_field)
    with output_path.open("w", encoding="utf-8") as destination:
        json.dump(cleaned, destination, ensure_ascii=False, indent=2)
        destination.write("\n")


def clean_jsonl_file(input_path: Path, output_path: Path, text_field: str) -> None:
    with input_path.open("r", encoding="utf-8") as source, output_path.open(
        "w", encoding="utf-8"
    ) as destination:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                destination.write(line)
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"第 {line_number} 行不是有效 JSON") from error
            cleaned = clean_json_value(record, text_field)
            destination.write(json.dumps(cleaned, ensure_ascii=False))
            destination.write("\n")


def clean_text_file(input_path: Path, output_path: Path) -> None:
    with input_path.open("r", encoding="utf-8") as source:
        content = source.read()
    with output_path.open("w", encoding="utf-8") as destination:
        destination.write(remove_emoji_markers(content))


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    output_path = Path(args.output_path)
    if not input_path.is_file():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = input_path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        clean_delimited_file(input_path, output_path, args.text_columns)
    elif suffix == ".json":
        clean_json_file(input_path, output_path, args.text_field)
    elif suffix == ".jsonl":
        clean_jsonl_file(input_path, output_path, args.text_field)
    elif suffix in {".txt", ".md"}:
        clean_text_file(input_path, output_path)
    else:
        raise ValueError("仅支持 txt、md、csv、tsv、json、jsonl 格式")

    print(f"[OK] 文本表情标识移除完成 -> {output_path}")


if __name__ == "__main__":
    main()
