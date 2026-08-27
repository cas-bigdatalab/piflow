from __future__ import annotations

import argparse
import csv
import math
import re
import unicodedata
from pathlib import Path
from typing import Any


_REQUIRED_FIELDS = {
    "contract_version",
    "dataset_name",
    "metric_key",
    "selected_count",
    "available_count",
    "mean_value",
    "min_value",
    "max_value",
    "unit",
}


def compare_metric_summaries(
    input_1: str | Path,
    input_2: str | Path,
    output_path: str | Path,
    *,
    difference_order: str = "input_2-input_1",
    output_file_name: str = "metric_summary_comparison.csv",
) -> dict[str, Any]:
    left = _read_summary(Path(input_1), "input_1")
    right = _read_summary(Path(input_2), "input_2")
    if left["metric_key"] != right["metric_key"]:
        raise ValueError(
            "METRIC_MISMATCH: "
            f"input_1={left['metric_key']!r}, input_2={right['metric_key']!r}"
        )
    if _canonical_unit(left["unit"]) != _canonical_unit(right["unit"]):
        raise ValueError(
            "UNIT_MISMATCH: "
            f"input_1={left['unit']!r}, input_2={right['unit']!r}"
        )

    normalized_order = _resolve_difference_order(
        difference_order,
        input_1_dataset=left["dataset_name"],
        input_2_dataset=right["dataset_name"],
    )
    if normalized_order == "input_2-input_1":
        minuend, subtrahend = right, left
    else:
        minuend, subtrahend = left, right

    denominator = float(subtrahend["mean_value"])
    if denominator == 0:
        raise ValueError(
            "ZERO_COMPARISON_DENOMINATOR: "
            f"dataset={subtrahend['dataset_name']!r}, mean_value=0"
        )
    result = {
        "contract_version": "metric_comparison_v1",
        "metric_key": left["metric_key"],
        "unit": left["unit"],
        "input_1_dataset": left["dataset_name"],
        "input_1_selected_count": int(left["selected_count"]),
        "input_1_available_count": int(left["available_count"]),
        "input_1_mean": float(left["mean_value"]),
        "input_1_min": float(left["min_value"]),
        "input_1_max": float(left["max_value"]),
        "input_2_dataset": right["dataset_name"],
        "input_2_selected_count": int(right["selected_count"]),
        "input_2_available_count": int(right["available_count"]),
        "input_2_mean": float(right["mean_value"]),
        "input_2_min": float(right["min_value"]),
        "input_2_max": float(right["max_value"]),
        "difference_order": normalized_order,
        "mean_difference": float(minuend["mean_value"]) - denominator,
        "mean_ratio": float(minuend["mean_value"]) / denominator,
        "result_file_name": Path(str(output_file_name)).name,
    }
    _write_csv_row(Path(output_path), result)
    return result


def _resolve_difference_order(
    difference_order: str,
    *,
    input_1_dataset: str,
    input_2_dataset: str,
) -> str:
    """把端口表达式或“数据集A_minus_数据集B”统一成标准端口方向。"""
    raw = unicodedata.normalize("NFKC", str(difference_order or "")).casefold().strip()
    compact = re.sub(r"\s+", "", raw)
    compact = compact.replace("−", "-").replace("–", "-").replace("—", "-")
    aliases = {
        "input_1-input_2": "input_1-input_2",
        "input1-input2": "input_1-input_2",
        "input_1_minus_input_2": "input_1-input_2",
        "input1_minus_input2": "input_1-input_2",
        "left-minus-right": "input_1-input_2",
        "left_minus_right": "input_1-input_2",
        "input_2-input_1": "input_2-input_1",
        "input2-input1": "input_2-input_1",
        "input_2_minus_input_1": "input_2-input_1",
        "input2_minus_input1": "input_2-input_1",
        "right-minus-left": "input_2-input_1",
        "right_minus_left": "input_2-input_1",
    }
    canonical = aliases.get(compact)
    if canonical is not None:
        return canonical

    semantic = _split_semantic_difference(compact)
    if semantic is not None:
        minuend_label, subtrahend_label = semantic
        minuend_port = _resolve_dataset_port(
            minuend_label,
            input_1_dataset=input_1_dataset,
            input_2_dataset=input_2_dataset,
        )
        subtrahend_port = _resolve_dataset_port(
            subtrahend_label,
            input_1_dataset=input_1_dataset,
            input_2_dataset=input_2_dataset,
        )
        if minuend_port == subtrahend_port:
            raise ValueError(
                "INVALID_DIFFERENCE_ORDER: minuend and subtrahend resolve to the same input; "
                f"difference_order={difference_order!r}"
            )
        return f"{minuend_port}-{subtrahend_port}"

    raise ValueError(
        "INVALID_DIFFERENCE_ORDER: expected input_1-input_2, input_2-input_1, "
        "or <dataset_label>_minus_<dataset_label>; "
        f"got {difference_order!r}, input_1_dataset={input_1_dataset!r}, "
        f"input_2_dataset={input_2_dataset!r}"
    )


def _split_semantic_difference(value: str) -> tuple[str, str] | None:
    for pattern in (
        r"^(.+?)_minus_(.+)$",
        r"^(.+?)-minus-(.+)$",
        r"^(.+?)minus(.+)$",
        r"^(.+?)减去(.+)$",
        r"^(.+?)减(.+)$",
    ):
        matched = re.fullmatch(pattern, value)
        if matched is not None:
            return matched.group(1), matched.group(2)
    return None


def _resolve_dataset_port(
    requested_label: str,
    *,
    input_1_dataset: str,
    input_2_dataset: str,
) -> str:
    requested = _canonical_dataset_label(requested_label)
    if not requested:
        raise ValueError("INVALID_DIFFERENCE_ORDER: dataset label must not be empty")

    matches: list[str] = []
    for port, dataset_name in (
        ("input_1", input_1_dataset),
        ("input_2", input_2_dataset),
    ):
        candidate = _canonical_dataset_label(dataset_name)
        if requested == candidate or (
            min(len(requested), len(candidate)) >= 4
            and (requested in candidate or candidate in requested)
        ):
            matches.append(port)

    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(
            "UNKNOWN_DIFFERENCE_DATASET: "
            f"label={requested_label!r}, input_1_dataset={input_1_dataset!r}, "
            f"input_2_dataset={input_2_dataset!r}"
        )
    raise ValueError(
        "AMBIGUOUS_DIFFERENCE_DATASET: "
        f"label={requested_label!r} matches both inputs; "
        f"input_1_dataset={input_1_dataset!r}, input_2_dataset={input_2_dataset!r}"
    )


def _canonical_dataset_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalized)


def _read_summary(path: Path, input_name: str) -> dict[str, str]:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"{input_name} summary not found: {source}")
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"INVALID_SUMMARY_ROW_COUNT: {input_name} requires exactly one row, got {len(rows)}")
    row = rows[0]
    missing = sorted(_REQUIRED_FIELDS - set(row))
    if missing:
        raise ValueError(f"INVALID_SUMMARY_CONTRACT: {input_name} missing fields {missing}")
    if row.get("contract_version") != "metric_summary_v1":
        raise ValueError(
            f"INVALID_SUMMARY_CONTRACT: {input_name} contract_version={row.get('contract_version')!r}"
        )
    for field in ("selected_count", "available_count"):
        try:
            value = int(row[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"INVALID_SUMMARY_NUMBER: {input_name}.{field}={row[field]!r}") from exc
        if value <= 0:
            raise ValueError(f"INVALID_SUMMARY_NUMBER: {input_name}.{field} must be greater than 0")
    for field in ("mean_value", "min_value", "max_value"):
        try:
            value = float(row[field])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"INVALID_SUMMARY_NUMBER: {input_name}.{field}={row[field]!r}") from exc
        if not math.isfinite(value):
            raise ValueError(f"INVALID_SUMMARY_NUMBER: {input_name}.{field} is not finite")
    return row


def _canonical_unit(unit: str) -> str:
    return str(unit).strip().casefold().replace(" ", "")


def _write_csv_row(output_path: Path, row: dict[str, Any]) -> None:
    target = output_path.expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow({key: _format_value(value) for key, value in row.items()})


def _format_value(value: Any) -> Any:
    return format(value, ".12g") if isinstance(value, float) else value


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two metric_summary_v1 CSV files.")
    parser.add_argument("--input_1", required=True)
    parser.add_argument("--input_2", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--difference_order", default="input_2-input_1")
    parser.add_argument("--output_file_name", default="metric_summary_comparison.csv")
    args = parser.parse_args()

    result = compare_metric_summaries(
        args.input_1,
        args.input_2,
        args.output,
        difference_order=args.difference_order,
        output_file_name=args.output_file_name,
    )
    print(
        "[OK] metric summaries compared: "
        f"metric={result['metric_key']}, difference={result['mean_difference']}, "
        f"ratio={result['mean_ratio']}, output={Path(args.output).resolve()}"
    )


if __name__ == "__main__":
    main()
