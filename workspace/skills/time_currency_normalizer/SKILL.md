---
name: time_currency_normalizer
name_zh: 时间货币归一算子
description: '时间/货币归一工具。读取结构化文本数据，将常见日期格式统一为YYYY-MM-DD，将$、€、¥/￥前缀金额转换为USD/EUR/CNY数值表达。

  当用户提到统一日期格式、标准化货币金额、清洗时间表述等需求时使用此skill。

  即使用户没有明确说出skill名，只要任务涉及日期或货币符号的归一化，就应该使用此skill。

  不负责汇率换算、时区转换或非前缀货币单位解析。

  '
tag: 清洗
input_params:
- name: input_path
  type: string
  required: true
  description: 输入结构化文件路径
- name: output_path
  type: string
  required: true
  description: 输出结构化文件路径
- name: text_columns
  type: string
  required: false
  description: 处理的文本列，逗号分隔；默认全部字符串列
- name: disable_date
  type: string
  required: false
  description: 关闭日期归一，仅保留货币归一
- name: disable_currency
  type: string
  required: false
  description: 关闭货币归一，仅保留日期归一
output_params:
- name: output_path
  type: string
  description: 日期/货币归一后的结构化文件
---

# Time Currency Normalizer 时间货币归一 Skill

## 功能概述

本skill对结构化数据中的文本列做时间和货币表达归一：常见日期格式统一为 `YYYY-MM-DD`；`$`、`€`、`¥/￥` 前缀金额统一为 `USD/EUR/CNY 金额`，并去掉金额千分位逗号。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 统一日期格式
- 标准化文本中的货币金额
- 清洗合同、票据、实验记录里的日期和金额表述
- 只关闭日期归一或只关闭货币归一的对照清洗

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input_path` | 输入CSV/TSV/Excel等结构化文件路径 |
| `--output_path` | 输出结构化文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text_columns` | 处理的文本列，逗号分隔；不填则处理全部字符串列 | 全部字符串列 |
| `--disable_date` | 关闭日期归一 | `False` |
| `--disable_currency` | 关闭货币归一 | `False` |

## 输入文件格式

支持CSV、TSV、Excel (.xls/.xlsx)、SPSS (.sav)。

不支持的文件格式会直接报错拒绝，不会自动猜测格式。

## 使用方法

```bash
python scripts/run_time_currency_normalizer.py \
  --input_path input.csv \
  --output_path output.csv \
  --text_columns text
```

## 处理示例

| 输入文本 | 输出文本 |
|----------|----------|
| `Meeting on 2024/1/2 costs $1,299.` | `Meeting on 2024-01-02 costs USD 1299.` |
| `合同签订于 2024年1月2日，金额为￥300。` | `合同签订于 2024-01-02，金额为CNY 300。` |
| `No date or money here.` | `No date or money here.` |

## 环境要求

依赖Python、pandas，以及本仓库DC公用`data_io`读写工具。

## 注意事项

1. `M/D/YYYY`与`D/M/YYYY`存在歧义时，首段大于12按日-月-年，否则按月-日-年。
2. 货币归一只处理`$`、`€`、`¥/￥`前缀金额，不做汇率换算。
3. 该skill不负责自然语言时间推断、时区转换或后缀货币单位解析。
