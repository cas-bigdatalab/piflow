import argparse
import json
import os
import re
from datetime import datetime

import pandas as pd

ALLOWED_RULE_KEYS = {
    "type",
    "required",
    "nullable",
    "enum",
    "min",
    "max",
    "min_length",
    "max_length",
    "pattern",
    "format",
    "properties",
    "items",
}
ALLOWED_TYPES = {"int", "float", "str", "bool", "date", "datetime", "object", "array"}


def read_data(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    file_ext = os.path.splitext(file_path)[1].lower()
    common_encodings = ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]

    if file_ext == ".csv":
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise ValueError("无法读取CSV文件")

    if file_ext == ".tsv":
        for encoding in common_encodings:
            try:
                return pd.read_csv(file_path, sep="\t", encoding=encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        raise ValueError("无法读取TSV文件")

    if file_ext in {".xlsx", ".xls"}:
        return pd.read_excel(file_path)

    if file_ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return pd.DataFrame(data)
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            return pd.DataFrame(data["data"])
        if isinstance(data, dict):
            return pd.DataFrame([data])
        raise ValueError("JSON 输入必须是对象、对象数组或包含 data 数组的对象")

    if file_ext == ".jsonl":
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return pd.DataFrame(records)

    raise ValueError(f"不支持的文件格式: {file_ext}")


def write_data(df: pd.DataFrame, output_path: str):
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_ext = os.path.splitext(output_path)[1].lower()
    if file_ext == ".csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    elif file_ext == ".tsv":
        df.to_csv(output_path, sep="\t", index=False, encoding="utf-8-sig")
    elif file_ext in {".xlsx", ".xls"}:
        df.to_excel(output_path, index=False)
    elif file_ext == ".json":
        df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    else:
        df.to_csv(output_path, index=False, encoding="utf-8-sig")


def is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def add_count(field_errors: dict, field: str, error_key: str, count: int = 1):
    field_bucket = field_errors.setdefault(field, {})
    field_bucket[error_key] = int(field_bucket.get(error_key, 0)) + int(count)


def add_sample(sample_errors: list, row, field: str, error: str, value, limit: int = 20):
    if len(sample_errors) >= limit:
        return
    if is_missing(value):
        sample_value = None
    else:
        sample_value = value if isinstance(value, (dict, list)) else str(value)[:100]
    sample_errors.append({"row": row, "field": field, "error": error, "value": sample_value})


def validate_rule_spec(rule: dict, field_path: str):
    if not isinstance(rule, dict):
        raise ValueError(f"字段 {field_path} 的 schema 必须是对象")

    unknown_keys = set(rule) - ALLOWED_RULE_KEYS
    if unknown_keys:
        unknown_text = ", ".join(sorted(unknown_keys))
        raise ValueError(f"字段 {field_path} 包含不支持的 schema 规则: {unknown_text}")

    if "type" in rule and rule["type"] not in ALLOWED_TYPES:
        raise ValueError(f"字段 {field_path} 的 type 不受支持: {rule['type']}")
    if "required" in rule and not isinstance(rule["required"], bool):
        raise ValueError(f"字段 {field_path} 的 required 必须是布尔值")
    if "nullable" in rule and not isinstance(rule["nullable"], bool):
        raise ValueError(f"字段 {field_path} 的 nullable 必须是布尔值")
    if "enum" in rule and not isinstance(rule["enum"], list):
        raise ValueError(f"字段 {field_path} 的 enum 必须是列表")
    if "min" in rule and not isinstance(rule["min"], (int, float)):
        raise ValueError(f"字段 {field_path} 的 min 必须是数值")
    if "max" in rule and not isinstance(rule["max"], (int, float)):
        raise ValueError(f"字段 {field_path} 的 max 必须是数值")
    if "min_length" in rule and not isinstance(rule["min_length"], int):
        raise ValueError(f"字段 {field_path} 的 min_length 必须是整数")
    if "max_length" in rule and not isinstance(rule["max_length"], int):
        raise ValueError(f"字段 {field_path} 的 max_length 必须是整数")
    if "pattern" in rule and not isinstance(rule["pattern"], str):
        raise ValueError(f"字段 {field_path} 的 pattern 必须是字符串")
    if "format" in rule and not isinstance(rule["format"], str):
        raise ValueError(f"字段 {field_path} 的 format 必须是字符串")
    if "format" in rule and rule.get("type") not in {"date", "datetime"}:
        raise ValueError(f"字段 {field_path} 只有 date/datetime 类型才能使用 format")
    if "properties" in rule:
        if rule.get("type") != "object":
            raise ValueError(f"字段 {field_path} 只有 object 类型才能使用 properties")
        if not isinstance(rule["properties"], dict) or not rule["properties"]:
            raise ValueError(f"字段 {field_path} 的 properties 必须是非空对象")
        for subfield, subrule in rule["properties"].items():
            validate_rule_spec(subrule, f"{field_path}.{subfield}")
    if "items" in rule:
        if rule.get("type") != "array":
            raise ValueError(f"字段 {field_path} 只有 array 类型才能使用 items")
        validate_rule_spec(rule["items"], f"{field_path}[]")


def parse_schema(schema_arg: str) -> dict:
    if os.path.exists(schema_arg):
        with open(schema_arg, "r", encoding="utf-8") as f:
            schema = json.load(f)
    else:
        schema = json.loads(schema_arg)

    if not isinstance(schema, dict):
        raise ValueError("schema 必须是 JSON 对象")

    fields = schema.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("schema 必须包含非空的 fields 对象")

    for field_name, rules in fields.items():
        validate_rule_spec(rules, field_name)

    table_constraints = schema.get("table_constraints", {})
    if table_constraints and not isinstance(table_constraints, dict):
        raise ValueError("table_constraints 必须是 JSON 对象")
    if "min_rows" in table_constraints and not isinstance(table_constraints["min_rows"], int):
        raise ValueError("table_constraints.min_rows 必须是整数")
    if "max_missing_ratio" in table_constraints and not isinstance(table_constraints["max_missing_ratio"], (int, float)):
        raise ValueError("table_constraints.max_missing_ratio 必须是数值")
    if "strict_columns" in table_constraints and not isinstance(table_constraints["strict_columns"], bool):
        raise ValueError("table_constraints.strict_columns 必须是布尔值")
    if "check_column_order" in table_constraints and not isinstance(table_constraints["check_column_order"], bool):
        raise ValueError("table_constraints.check_column_order 必须是布尔值")

    schema["table_constraints"] = table_constraints
    return schema


class SchemaValidator:
    def __init__(self, schema: dict):
        self.fields = schema["fields"]
        self.table_constraints = schema.get("table_constraints", {})

    def _parse_scalar(self, value, expected_type: str, rules: dict):
        if expected_type == "int":
            if isinstance(value, bool):
                return None, False
            if isinstance(value, int):
                return value, True
            if isinstance(value, float):
                if float(value).is_integer():
                    return int(value), True
                return None, False
            try:
                text = str(value).strip()
                number = float(text)
                if number.is_integer():
                    return int(number), True
            except Exception:
                return None, False
            return None, False

        if expected_type == "float":
            if isinstance(value, bool):
                return None, False
            if isinstance(value, (int, float)):
                return float(value), True
            try:
                return float(str(value).strip()), True
            except Exception:
                return None, False

        if expected_type == "str":
            return (value, True) if isinstance(value, str) else (None, False)

        if expected_type == "bool":
            if isinstance(value, bool):
                return value, True
            if isinstance(value, (int, float)) and value in {0, 1}:
                return bool(value), True
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "false", "1", "0"}:
                    return normalized in {"true", "1"}, True
            return None, False

        if expected_type in {"date", "datetime"}:
            fmt = rules.get("format")
            if isinstance(value, (datetime, pd.Timestamp)):
                return value, True
            if isinstance(value, str):
                text = value.strip()
                try:
                    if fmt:
                        return datetime.strptime(text, fmt), True
                    return datetime.fromisoformat(text), True
                except Exception:
                    return None, False
            return None, False

        if expected_type == "object":
            return (value, True) if isinstance(value, dict) else (None, False)

        if expected_type == "array":
            return (value, True) if isinstance(value, list) else (None, False)

        return None, False

    def _validate_rule(self, value, rules: dict, field_path: str):
        errors = []
        expected_type = rules.get("type")
        parsed_value = value

        if is_missing(value):
            if rules.get("required", False):
                return ["missing_required_field"], None
            if rules.get("nullable", True) is False:
                return ["null_not_allowed"], None
            return [], None

        if expected_type:
            parsed_value, type_ok = self._parse_scalar(value, expected_type, rules)
            if not type_ok:
                return ["type_error"], None

        if "enum" in rules and parsed_value not in rules["enum"]:
            errors.append("enum_error")

        if expected_type in {"int", "float"}:
            numeric_value = float(parsed_value)
            if "min" in rules and numeric_value < rules["min"]:
                errors.append("range_error")
            if "max" in rules and numeric_value > rules["max"]:
                errors.append("range_error")

        if "min_length" in rules or "max_length" in rules:
            text_value = parsed_value if isinstance(parsed_value, str) else str(parsed_value)
            if "min_length" in rules and len(text_value) < rules["min_length"]:
                errors.append("length_error")
            if "max_length" in rules and len(text_value) > rules["max_length"]:
                errors.append("length_error")

        if "pattern" in rules:
            text_value = parsed_value if isinstance(parsed_value, str) else str(parsed_value)
            if re.fullmatch(rules["pattern"], text_value) is None:
                errors.append("pattern_error")

        if expected_type in {"date", "datetime"} and "format" in rules:
            if not isinstance(parsed_value, (datetime, pd.Timestamp)):
                errors.append("date_format_error")

        if expected_type == "object" and "properties" in rules and isinstance(parsed_value, dict):
            for subfield, subrule in rules["properties"].items():
                subpath = f"{field_path}.{subfield}"
                subvalue = parsed_value.get(subfield)
                sub_errors, _ = self._validate_rule(subvalue, subrule, subpath)
                errors.extend([f"{subpath}:{err}" for err in sub_errors])

        if expected_type == "array" and "items" in rules and isinstance(parsed_value, list):
            for idx, item in enumerate(parsed_value):
                subpath = f"{field_path}[{idx}]"
                sub_errors, _ = self._validate_rule(item, rules["items"], subpath)
                errors.extend([f"{subpath}:{err}" for err in sub_errors])

        return errors, parsed_value

    def _field_missing_ratio(self, df: pd.DataFrame, field_names: list[str]) -> dict:
        ratios = {}
        for field in field_names:
            if field not in df.columns:
                ratios[field] = 1.0
                continue
            ratios[field] = float(df[field].isna().mean()) if len(df) > 0 else 1.0
        return ratios

    def perform(self, input_path: str, output_path: str, output_invalid: str = None):
        df = read_data(input_path)
        total_rows = len(df)
        actual_columns = list(df.columns)
        expected_columns = list(self.fields.keys())
        table_constraints = self.table_constraints

        field_errors = {}
        schema_errors = []
        sample_errors = []
        invalid_indices = set()

        min_rows = table_constraints.get("min_rows")
        if min_rows is not None and total_rows < min_rows:
            add_count(field_errors, "__table__", "row_count_below_min", 1)
            schema_errors.append({
                "field": "__table__",
                "error": "row_count_below_min",
                "expected": min_rows,
                "actual": total_rows,
            })
            add_sample(sample_errors, None, "__table__", "row_count_below_min", {"expected": min_rows, "actual": total_rows})
            invalid_indices.update(range(total_rows))

        strict_columns = table_constraints.get("strict_columns", False)
        check_column_order = table_constraints.get("check_column_order", False)
        max_missing_ratio = table_constraints.get("max_missing_ratio")

        missing_fields = [field for field in expected_columns if field not in actual_columns]
        if missing_fields:
            for field in missing_fields:
                add_count(field_errors, field, "missing_required_field", total_rows)
                schema_errors.append({
                    "field": field,
                    "error": "missing_required_field",
                    "expected": "present",
                    "actual": "missing",
                })
                add_sample(sample_errors, None, field, "missing_required_field", None)
            invalid_indices.update(range(total_rows))

        if strict_columns:
            unexpected_fields = [col for col in actual_columns if col not in self.fields]
            for col in unexpected_fields:
                add_count(field_errors, col, "unexpected_field", total_rows)
                schema_errors.append({
                    "field": col,
                    "error": "unexpected_field",
                    "expected": "not present",
                    "actual": "present",
                })
                add_sample(sample_errors, None, col, "unexpected_field", None)
            if unexpected_fields:
                invalid_indices.update(range(total_rows))
        else:
            unexpected_fields = [col for col in actual_columns if col not in self.fields]

        if check_column_order and set(actual_columns) == set(expected_columns) and actual_columns != expected_columns:
            add_count(field_errors, "__schema__", "order_error", total_rows)
            schema_errors.append({
                "field": "__schema__",
                "error": "order_error",
                "expected": expected_columns,
                "actual": actual_columns,
            })
            add_sample(sample_errors, None, "__schema__", "order_error", {"expected": expected_columns, "actual": actual_columns})
            invalid_indices.update(range(total_rows))

        for field, rules in self.fields.items():
            if field not in df.columns:
                continue

            for row_pos, (idx, value) in enumerate(df[field].items()):
                row_errors, _ = self._validate_rule(value, rules, field)
                if row_errors:
                    invalid_indices.add(row_pos)
                for row_error in row_errors:
                    if ":" in row_error:
                        field_path, error_name = row_error.split(":", 1)
                    else:
                        field_path, error_name = field, row_error
                    add_count(field_errors, field_path, error_name)
                    add_sample(sample_errors, row_pos, field_path, error_name, value)

        field_missing_ratios = self._field_missing_ratio(df, list(self.fields.keys()))
        if max_missing_ratio is not None:
            missing_ok = True
            for field_name, ratio in field_missing_ratios.items():
                if ratio > max_missing_ratio:
                    missing_ok = False
                    add_count(field_errors, field_name, "missing_ratio_exceeded", 1)
                    schema_errors.append({
                        "field": field_name,
                        "error": "missing_ratio_exceeded",
                        "expected": max_missing_ratio,
                        "actual": round(ratio, 6),
                    })
                    add_sample(sample_errors, None, field_name, "missing_ratio_exceeded", {"ratio": ratio, "threshold": max_missing_ratio})
            if not missing_ok:
                invalid_indices.update(range(total_rows))

        valid_rows = total_rows - len(invalid_indices)
        validation_rate = (valid_rows / total_rows * 100) if total_rows > 0 else 100.0

        report = {
            "summary": {
                "total_rows": int(total_rows),
                "valid_rows": int(valid_rows),
                "invalid_rows": int(len(invalid_indices)),
                "validation_rate": round(validation_rate, 2),
            },
            "schema_errors": schema_errors,
            "field_errors": {field: {name: int(count) for name, count in errors.items()} for field, errors in field_errors.items()},
            "sample_errors": sample_errors[:20],
        }

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        if output_invalid and output_invalid.strip() and invalid_indices:
            invalid_df = df.iloc[sorted(invalid_indices)]
            write_data(invalid_df, output_invalid.strip())

        print("[OK] Schema validation completed")
        print(f"  Input file: {input_path}")
        print(f"  Output report: {output_path}")
        print(f"  Total rows: {total_rows}")
        print(f"  Valid rows: {valid_rows}")
        print(f"  Invalid rows: {len(invalid_indices)}")
        print(f"  Validation rate: {validation_rate:.1f}%")
        if schema_errors:
            print("  Schema errors:")
            for item in schema_errors:
                print(f"    - {item['field']}: {item['error']}")
        if output_invalid and output_invalid.strip() and invalid_indices:
            print(f"  Invalid data exported to: {output_invalid.strip()}")


def main():
    parser = argparse.ArgumentParser(description="SchemaValidator - 显式 schema 校验工具")
    parser.add_argument("--input", required=True, type=str, help="输入文件路径")
    parser.add_argument("--output", required=True, type=str, help="验证报告输出路径")
    parser.add_argument("--schema", required=True, type=str, help="schema 定义（JSON 字符串或文件路径）")
    parser.add_argument("--output_invalid", type=str, default="", help="无效数据输出路径（可选）")

    args = parser.parse_args()
    schema = parse_schema(args.schema)
    validator = SchemaValidator(schema)
    validator.perform(
        input_path=args.input,
        output_path=args.output,
        output_invalid=args.output_invalid,
    )


if __name__ == "__main__":
    main()
