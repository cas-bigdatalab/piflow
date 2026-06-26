---
name: data_masking
description: '数据脱敏工具。对结构化数据中的敏感字段进行字符遮蔽脱敏，保留字段位置并用遮蔽字符替换手机号、身份证、姓名、邮箱、银行卡等内容。

  当用户提到数据脱敏、隐私保护、敏感字段遮蔽、PII 处理等需求时使用此 skill。

  与 privacy_token_remover 区分开：本 skill 负责字段级遮蔽，不负责删除文本中的隐私标识，也不负责生成假数据。

  '
name_zh: 数据脱敏算子
input_params:
- name: input
  type: string
  required: true
  description: 输入文件路径（支持 CSV/TSV/Excel 等）
- name: output
  type: string
  required: true
  description: 输出文件路径
- name: masking_rules
  type: string
  required: true
  description: 脱敏规则，格式：字段名:脱敏类型，多个规则用逗号分隔
- name: mask_char
  type: string
  required: false
  default: '*'
  description: 脱敏替换字符
output_params:
- name: output
  type: csv_file
  description: 脱敏后的结构化数据文件
tag: 清洗
---

# Data Masking 数据脱敏 Skill

## 功能概述

本 skill 用于对结构化数据中的敏感信息进行脱敏处理，使用字符遮蔽模式（如 `138****5678`）。
如需用假数据替换敏感信息，请使用 data_faker。

## 触发条件

当用户请求以下任务时，应使用此 skill：
- 数据脱敏
- 隐私保护
- 敏感信息处理
- 数据匿名化
- PII（个人可识别信息）处理

## 核心参数说明

### 必需参数
- `--input`：输入文件路径
- `--output`：输出文件路径
- `--masking_rules`：脱敏规则，格式为 `字段名:脱敏类型`

### 可选参数
- `--mask_char`：脱敏替换字符，默认 `*`

## 输入文件格式

支持 CSV、TSV、Excel 等结构化数据。

## 使用方法

```bash
python scripts/run_data_masking.py \
  --input data.csv \
  --output masked.csv \
  --masking_rules "phone:phone,idcard:idcard,name:name"
```

```bash
python scripts/run_data_masking.py \
  --input data.csv \
  --output masked.csv \
  --masking_rules "email:email" \
  --mask_char "#"
```

## 输出示例

```
[OK] Data masking completed!
   Input file: data.csv
   Output file: masked.csv
   Total rows: 1000
   Masking rules applied:
     - phone: phone (1000 values masked)
     - idcard: idcard (1000 values masked)
     - name: name (1000 values masked)
   Mode: mask (char: *)
```

## 脱敏效果示例

| 原始值 | 脱敏后 |
|--------|--------|
| `13812345678` | `138****5678` |
| `110101199001011234` | `110101********1234` |
| `张三` | `张*` |
| `test@example.com` | `te**@example.com` |
| `user@example.com` | `us**@example.com` |

## 环境要求

```bash
pip install pandas openpyxl
```

## 注意事项

1. 脱敏规则格式必须正确：`字段名:脱敏类型`
2. 字段名必须存在于数据中
3. 脱敏后的数据不可逆，请备份原始数据
4. 建议在测试环境验证脱敏效果后再处理生产数据
