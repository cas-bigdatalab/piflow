---
name: schema_validator
description: '显式 schema 校验工具。读取结构化数据与用户提供的 schema，检查字段存在性、字段类型、枚举、范围、长度、正则格式、日期格式、表级行数与缺失率约束，并输出校验报告。

  当用户提到 schema 校验、结构校验、模式校验、字段存在性检查、字段类型检查、枚举校验、范围校验、格式校验、表头结构校验等需求时使用此 skill。

  即使用户没有明确说出"schema_validator"，只要任务是在检查结构化数据是否符合明确 schema 规则，就应该使用此 skill。

  不负责数据清洗、去重、业务合理性判断、跨字段一致性、参照完整性、分布异常分析或数据转换。

  '
name_zh: 显式 Schema 校验器
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持 CSV/TSV/Excel/JSON/JSONL）
- name: output
  type: string
  required: true
  description: 验证报告输出路径
- name: schema
  type: string
  required: true
  description: schema 定义（JSON 字符串或文件路径，必须包含 fields，可选 table_constraints）
- name: output_invalid
  type: string
  required: false
  default: ''
  description: 无效数据输出路径（可选）
output_params:
- name: output
  type: json_file
  description: 验证报告文件
- name: output_invalid
  type: file
  description: 无效数据输出文件
tag: 校验
---

# Schema Validator 显式 schema 校验 Skill

## 功能概述

本 skill 用于验证结构化数据是否符合用户提供的明确 schema 规则。它检查字段是否存在、类型是否匹配、枚举值是否合规、数值是否超出范围、字符串长度是否合规、正则格式是否匹配、日期格式是否正确，以及嵌套对象/数组结构是否符合定义。它还支持表级约束，例如最小行数、最大缺失率、字段顺序与额外字段控制。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- schema 校验
- 结构校验
- 模式校验
- 字段存在性检查
- 字段类型检查
- 枚举校验
- 范围校验
- 格式校验
- 表头结构校验

## schema 定义格式

```json
{
  "fields": {
    "id": {
      "type": "int",
      "required": true,
      "nullable": false
    },
    "name": {
      "type": "str",
      "required": true,
      "min_length": 1,
      "max_length": 100
    },
    "status": {
      "type": "str",
      "enum": ["active", "inactive", "pending"]
    },
    "score": {
      "type": "float",
      "min": 0,
      "max": 100
    },
    "email": {
      "type": "str",
      "pattern": "^[\\w.-]+@[\\w.-]+\\.\\w+$"
    },
    "created_at": {
      "type": "date",
      "format": "%Y-%m-%d"
    }
  },
  "table_constraints": {
    "min_rows": 10,
    "max_missing_ratio": 0.2,
    "strict_columns": true,
    "check_column_order": true
  }
}
```

## 支持的验证规则

| 规则 | 说明 | 适用类型 |
|------|------|---------|
| `type` | 数据类型 | 所有 |
| `required` | 是否必填 | 所有 |
| `nullable` | 是否允许空值 | 所有 |
| `min` | 最小值 | int, float |
| `max` | 最大值 | int, float |
| `min_length` | 最小长度 | str |
| `max_length` | 最大长度 | str |
| `pattern` | 正则表达式 | str |
| `enum` | 枚举值列表 | str, int |
| `format` | 日期/日期时间格式 | date, datetime |
| `min_rows` | 最小行数 | table_constraints |
| `max_missing_ratio` | 最大缺失率 | table_constraints |
| `strict_columns` | 禁止额外字段 | table_constraints |
| `check_column_order` | 校验字段顺序 | table_constraints |

## 使用方法

### 使用内联 schema
```bash
python scripts/run_schema_validator.py \
  --input data.csv \
  --output report.json \
  --schema '{"fields":{"id":{"type":"int","required":true},"name":{"type":"str","required":true}},"table_constraints":{"min_rows":10,"max_missing_ratio":0.2}}'
```

### 使用 schema 文件
```bash
python scripts/run_schema_validator.py \
  --input data.csv \
  --output report.json \
  --schema schema.json
```

### 导出无效数据
```bash
python scripts/run_schema_validator.py \
  --input data.csv \
  --output report.json \
  --schema schema.json \
  --output_invalid invalid_rows.csv
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input` | 是 | 输入文件路径 |
| `--output` | 是 | 验证报告路径 |
| `--schema` | 是 | schema 定义 |
| `--output_invalid` | 否 | 无效数据输出路径 |

## 输出示例

验证报告（JSON）：
```json
{
  "summary": {
    "total_rows": 1000,
    "valid_rows": 950,
    "invalid_rows": 50,
    "validation_rate": 95.0
  },
  "schema_errors": [
    {"field": "status", "error": "missing_required_field", "expected": "present", "actual": "missing"}
  ],
  "field_errors": {
    "id": {"type_error": 3},
    "email": {"pattern_error": 42}
  },
  "sample_errors": [
    {"row": 10, "field": "email", "error": "pattern_error", "value": "invalid-email"}
  ]
}
```
