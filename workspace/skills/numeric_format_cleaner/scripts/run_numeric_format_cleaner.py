import argparse
import json
import os
import re
from typing import Any, Dict, List, Tuple, Optional, Union


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    if not os.path.exists(path):
        return []
    items = []
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


def save_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    """保存JSONL文件"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_value_with_unit(value: Union[str, int, float, None]) -> Tuple[Optional[float], str]:
    """
    解析带单位的数值
    返回: (数值, 单位)
    """
    if value is None:
        return None, ""
    
    if isinstance(value, (int, float)):
        return float(value), ""
    
    value_str = str(value).strip()
    if not value_str:
        return None, ""
    
    # 匹配数值+单位的模式
    # 支持: 100km, 1.5kg, 2.3e-5, 10%, 1,000.50
    match = re.match(r'^([+-]?[\d\s,.eE+-]+)\s*([a-zA-Z%]*)$', value_str)
    if match:
        num_part = match.group(1).replace(',', '').replace(' ', '')
        unit_part = match.group(2)
        try:
            return float(num_part), unit_part
        except ValueError:
            return None, value_str
    
    return None, value_str


def convert_unit(value: float, from_unit: str, to_unit: str, conversion_rules: Dict[str, float]) -> Tuple[float, bool]:
    """
    单位转换
    返回: (转换后数值, 是否成功)
    """
    if not from_unit:
        return value, True
    
    if from_unit == to_unit:
        return value, False
    
    # 查找转换规则
    key = f"{from_unit}::{to_unit}"
    if key in conversion_rules:
        return value * conversion_rules[key], True
    
    # 尝试通用规则（如 km→m = 1000）
    common_rules = {
        ("km", "m"): 1000,
        ("m", "km"): 0.001,
        ("kg", "g"): 1000,
        ("g", "kg"): 0.001,
        ("mg", "g"): 0.001,
        ("mg", "kg"): 0.000001,
        ("cm", "m"): 0.01,
        ("mm", "m"): 0.001,
        ("km2", "m2"): 1000000,
        ("m2", "km2"): 0.000001,
        ("h", "s"): 3600,
        ("min", "s"): 60,
        ("d", "h"): 24,
        ("y", "d"): 365,
        ("%", "decimal"): 0.01,
        ("decimal", "%"): 100,
        ("°C", "K"): lambda x: x + 273.15,
        ("K", "°C"): lambda x: x - 273.15,
    }
    
    rule_key = (from_unit.lower(), to_unit.lower())
    if rule_key in common_rules:
        factor = common_rules[rule_key]
        if callable(factor):
            return factor(value), True
        return value * factor, True
    
    return value, False


def format_number(value: float, format_type: str, decimal_places: int, use_thousands_separator: bool) -> str:
    """
    格式化数值
    """
    if format_type == "scientific":
        formatted = f"{value:.{decimal_places}e}"
    elif format_type == "percent":
        formatted = f"{value * 100:.{decimal_places}f}"
    else:  # standard
        formatted = f"{value:.{decimal_places}f}"
    
    if use_thousands_separator and format_type == "standard":
        # 添加千分位分隔符
        parts = formatted.split('.')
        int_part = parts[0]
        int_part = int_part.replace(',', '')
        # 添加千分位
        int_part = "{:,}".format(int(int_part))
        if len(parts) > 1:
            formatted = f"{int_part}.{parts[1]}"
        else:
            formatted = int_part
    
    return formatted


def is_null_like(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "na", "n/a", "null", "none", "nan"}
    return False


def clean_numeric_value(value: Any, rules: Dict[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    """
    清洗单个数值
    返回: (清洗后值, 变更记录)
    """
    changes = {}
    
    if is_null_like(value):
        if rules.get("fill_null") not in (None, ""):
            return rules["fill_null"], {"filled": True, "original": value}
        return value, {}

    # 解析数值和单位
    num, unit = parse_value_with_unit(value)
    
    if num is None:
        # 无法解析，返回原始值
        return value, {"parse_error": True}
    
    original_num = num
    
    # 单位转换
    target_unit = rules.get("target_unit", "")
    if target_unit and unit:
        conversion_rules = rules.get("conversion_rules", {})
        num, converted = convert_unit(num, unit, target_unit, conversion_rules)
        if converted:
            changes["unit_converted"] = {"from": unit, "to": target_unit}
            unit = target_unit
    
    # 范围限制
    min_val = rules.get("min_value")
    max_val = rules.get("max_value")
    clamped = False
    
    if min_val is not None and num < min_val:
        if rules.get("clamp_to_range", False):
            num = min_val
            clamped = True
            changes["clamped_min"] = min_val
    
    if max_val is not None and num > max_val:
        if rules.get("clamp_to_range", False):
            num = max_val
            clamped = True
            changes["clamped_max"] = max_val
    
    # 格式转换
    format_type = rules.get("format_type", "standard")
    decimal_places = rules.get("decimal_places", 2)
    use_thousands = rules.get("use_thousands_separator", False)
    
    formatted = format_number(num, format_type, decimal_places, use_thousands)
    
    # 如果原始值有单位，保留单位
    if unit and not rules.get("strip_unit", False):
        if format_type != "percent":
            formatted = f"{formatted}{unit}"
    elif format_type == "percent":
        formatted = f"{formatted}%"
    
    if formatted != str(value):
        changes["formatted"] = True
        changes["original_value"] = value
    
    return formatted, changes


def process(args: argparse.Namespace) -> Dict[str, Any]:
    """处理主函数"""
    data = load_jsonl(args.input)
    
    # 解析字段规则
    field_rules = {}
    if args.field_rules:
        try:
            field_rules = json.loads(args.field_rules)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid field_rules JSON: {args.field_rules}")
            return {}
    
    # 解析全局转换规则
    conversion_rules = {}
    if args.conversion_rules:
        try:
            conversion_rules = json.loads(args.conversion_rules)
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid conversion_rules JSON: {args.conversion_rules}")
            return {}
    
    processed_count = 0
    total_changes = 0
    errors = 0
    
    results = []
    
    for item in data:
        new_item = item.copy()
        item_changes = {}
        
        for field, rules_template in field_rules.items():
            if field not in item:
                continue
            
            # 构建完整规则
            rules = rules_template.copy()
            rules["conversion_rules"] = conversion_rules
            
            # 应用全局默认值
            if "decimal_places" not in rules:
                rules["decimal_places"] = args.decimal_places
            if "fill_null" not in rules:
                rules["fill_null"] = args.fill_null
            
            try:
                cleaned_value, changes = clean_numeric_value(item[field], rules)
                
                if changes:
                    new_item[field] = cleaned_value
                    item_changes[field] = changes
                    total_changes += 1
                    
                    if changes.get("parse_error"):
                        errors += 1
            except Exception as e:
                print(f"[WARN] Error cleaning field {field}: {e}")
                errors += 1
                item_changes[field] = {"error": str(e)}
        
        if item_changes:
            processed_count += 1
            if args.mark_cleaned:
                new_item["_numeric_cleaned"] = True
                new_item["_numeric_changes"] = item_changes
        
        results.append(new_item)
    
    # 保存结果
    save_jsonl(args.output, results)
    
    # 保存统计
    stats = {
        "input": args.input,
        "output": args.output,
        "total_samples": len(data),
        "processed_samples": processed_count,
        "total_field_changes": total_changes,
        "errors": errors,
        "field_rules_applied": len(field_rules)
    }
    
    if args.stats_output:
        os.makedirs(os.path.dirname(args.stats_output) or ".", exist_ok=True)
        with open(args.stats_output, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("[OK] Numeric format cleaning completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total samples: {len(data)}")
    print(f"   Samples with changes: {processed_count}")
    print(f"   Total field changes: {total_changes}")
    print(f"   Errors: {errors}")
    
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Numeric format cleaner - 数值格式清洗（单位统一、格式规整）")
    parser.add_argument("--input", required=True, help="输入JSONL文件路径")
    parser.add_argument("--output", required=True, help="输出JSONL文件路径")
    parser.add_argument("--field_rules", required=True, help="字段清洗规则（JSON格式）")
    parser.add_argument("--conversion_rules", default="", help="单位转换规则（JSON格式）")
    parser.add_argument("--decimal_places", type=int, default=2, help="默认小数位数")
    parser.add_argument("--fill_null", default="", help="空值填充值")
    parser.add_argument("--mark_cleaned", type=str_to_bool, default=True, help="标记已清洗样本")
    parser.add_argument("--stats_output", default="numeric_format_cleaner_stats.json", help="统计输出文件路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process(args)


if __name__ == "__main__":
    main()
