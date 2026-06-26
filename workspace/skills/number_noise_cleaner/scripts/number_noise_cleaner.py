import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# 复用已有的结构化读写工具
CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

NUMBER_PATTERN = re.compile(r"(?<!\w)(?:\d+(?:\.\d+)?(?:/\d+)?(?:e[+-]?\d+)?)(?!\w)", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s{2,}")
SPACE_BEFORE_PUNCT_PATTERN = re.compile(r"\s+([,.;:!?，。；：！？])")
IDENTIFIER_PREFIXES = {"id", "no", "编号", "样本", "批次", "版本", "实验", "试验"}


@dataclass(frozen=True)
class NumberNoiseRules:
    preserve_years: bool = True
    year_min: int = 1900
    year_max: int = 2099
    preserve_identifiers: bool = True
    identifier_markers: tuple[str, ...] = ()
    preserve_measurements: bool = True
    measurement_units: tuple[str, ...] = ()


def parse_csv_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _select_columns(df: pd.DataFrame, text_columns: str | None) -> list[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def _is_year(token: str, rules: NumberNoiseRules) -> bool:
    if not token.isdigit() or len(token) != 4:
        return False
    value = int(token)
    return rules.preserve_years and rules.year_min <= value <= rules.year_max


def _has_identifier_context(text: str, start: int, end: int, rules: NumberNoiseRules) -> bool:
    if not rules.preserve_identifiers:
        return False

    left = text[max(0, start - 12):start]
    right = text[end:end + 12]
    around = (left + text[start:end] + right).lower()
    markers = tuple(marker.lower() for marker in rules.identifier_markers)
    if any(marker and marker in around for marker in markers):
        return True

    prev_char = text[start - 1] if start > 0 else ""
    next_char = text[end] if end < len(text) else ""
    if prev_char.isalpha() or next_char.isalpha():
        return True
    if prev_char in {".", "-", "_", "/"} and (start > 1 and text[start - 2].isalpha()):
        return True
    if next_char in {".", "-", "_", "/"} and (end + 1 < len(text) and text[end + 1].isalpha()):
        return True
    return False


def _has_measurement_context(text: str, start: int, end: int, rules: NumberNoiseRules) -> bool:
    if not rules.preserve_measurements:
        return False

    token = text[start:end]
    if "." in token or "/" in token or token.lower().startswith("0x"):
        return True
    if re.fullmatch(r"\d+%", token):
        return True
    if re.fullmatch(r"\d+(?:\.\d+)?e[+-]?\d+", token, flags=re.IGNORECASE):
        return True

    tail = text[end:]
    if not tail:
        return False

    units = [re.escape(unit.lower()) for unit in rules.measurement_units if unit]
    if not units:
        return False
    pattern = r"^\s*(?:" + "|".join(sorted(units, key=len, reverse=True)) + r")(?![A-Za-z])"
    return re.match(pattern, tail.lower()) is not None


def _looks_like_identifier_prefix(text: str, start: int) -> bool:
    left = text[max(0, start - 8):start].lower().strip(" .:-_/\t")
    if not left:
        return False
    last_token = re.split(r"\s+", left)[-1]
    if last_token == "id":
        return True
    if last_token in {"no", "编号", "样本", "批次", "版本", "实验", "试验"}:
        return True
    return False


def _should_preserve_number(text: str, start: int, end: int, token: str, rules: NumberNoiseRules) -> bool:
    if _is_year(token, rules):
        return True
    if _has_identifier_context(text, start, end, rules):
        return True
    if _looks_like_identifier_prefix(text, start):
        return True
    if _has_measurement_context(text, start, end, rules):
        return True
    return False


def _remove_number_noise(text: str, rules: NumberNoiseRules) -> str:
    result_parts: list[str] = []
    cursor = 0

    for match in NUMBER_PATTERN.finditer(text):
        start, end = match.span()
        token = match.group(0)
        if _should_preserve_number(text, start, end, token, rules):
            continue
        result_parts.append(text[cursor:start])
        cursor = end

    result_parts.append(text[cursor:])
    cleaned = "".join(result_parts)

    cleaned = SPACE_BEFORE_PUNCT_PATTERN.sub(r"\1", cleaned)
    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)
    cleaned = re.sub(r"\n\s+", "\n", cleaned)
    return cleaned.strip()


def number_noise_clean(input_path: str, output_path: str, text_columns: str | None, rules: NumberNoiseRules):
    df = read_structured_data(input_path)
    target_cols = _select_columns(df, text_columns)

    if not target_cols:
        print("[WARN] 未选中任何文本字段，数据将原样输出。")
    else:
        for col in target_cols:
            df[col] = df[col].apply(lambda v: _remove_number_noise(str(v), rules) if pd.notna(v) and isinstance(v, str) else v)

    write_structured_data(df, output_path)
    print(
        f"[OK] 无用数字字符清理完成 -> {output_path}\n"
        f"   处理列: {target_cols if target_cols else '无'}\n"
        f"   行数: {len(df)}"
    )


def main():
    parser = argparse.ArgumentParser(description="无用数字字符清理：移除无语义的独立数字 token")
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument(
        "--text_columns",
        required=False,
        default=None,
        help="需清洗的文本列，逗号分隔；若不指定则默认处理所有字符串列",
    )
    parser.add_argument("--preserve_years", required=False, default="true", help="是否保留年份，默认 true")
    parser.add_argument("--year_min", required=False, type=int, default=1900, help="年份保留下限")
    parser.add_argument("--year_max", required=False, type=int, default=2099, help="年份保留上限")
    parser.add_argument("--preserve_identifiers", required=False, default="true", help="是否保留编号/版本号等标识，默认 true")
    parser.add_argument(
        "--identifier_markers",
        required=False,
        default="ID,No.,No,编号,样本,批次,版本,实验,试验",
        help="编号上下文标记，逗号分隔",
    )
    parser.add_argument("--preserve_measurements", required=False, default="true", help="是否保留实验数值/单位数值，默认 true")
    parser.add_argument(
        "--measurement_units",
        required=False,
        default="%,mg,g,kg,ug,μg,mL,ml,L,℃,°C,mol,mm,cm,m,h,s,min",
        help="实验数值单位，逗号分隔",
    )

    args = parser.parse_args()
    rules = NumberNoiseRules(
        preserve_years=str(args.preserve_years).lower() in {"true", "1", "yes"},
        year_min=args.year_min,
        year_max=args.year_max,
        preserve_identifiers=str(args.preserve_identifiers).lower() in {"true", "1", "yes"},
        identifier_markers=parse_csv_list(args.identifier_markers),
        preserve_measurements=str(args.preserve_measurements).lower() in {"true", "1", "yes"},
        measurement_units=parse_csv_list(args.measurement_units),
    )
    number_noise_clean(args.input_path, args.output_path, args.text_columns, rules)


if __name__ == "__main__":
    main()
