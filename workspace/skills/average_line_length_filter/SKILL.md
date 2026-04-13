---
name: average_line_length_filter
description: |
  平均行长度过滤器。过滤文本平均行长度不在指定范围内的样本。
  当用户提到行长度过滤、平均行长度、文本行长度筛选、按行筛选等需求时使用此skill。
  即使用户没有明确说出"平均行长度"，只要任务涉及根据文本中每行的平均长度来筛选数据，
  就应该使用此skill。
---

# Average Line Length Filter 平均行长度过滤 Skill

## 功能概述

本skill根据文本的平均行长度进行过滤，只保留平均行长度在指定范围内的样本。
常用于过滤过短或过长的文本行、清理格式不规范的文本等场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 行长度过滤
- 平均行长度筛选
- 文本行长度过滤
- 按行筛选
- 清理过长文本
- 清理过短文本

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--min_len` | 最小平均行长度 | `10` |
| `--max_len` | 最大平均行长度 | `无限制` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {"text": "第一行\n第二行\n第三行"},
  {"text": "只有一行"},
  {"text": "长文本内容\n带有换行"}
]
```

## 使用方法

### 过滤平均行长度在10-100之间的样本（默认）
```bash
python scripts/run_average_line_length_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 过滤平均行长度在20-50之间的样本
```bash
python scripts/run_average_line_length_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_len 20 \
  --max_len 50
```

### 只设置最小长度（无上限）
```bash
python scripts/run_average_line_length_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_len 15
```

## 过滤示例

| 文本 | 行数 | 平均行长度 | 过滤结果 (10-20) |
|------|------|-----------|------------------|
| `a=1\nb\nc=1+2+3\nd=6` | 4 | 4 | 过滤 |
| `Today is Sund Sunda and it's a happy day!\nYou know` | 2 | 26 | 过滤 |
| `a v s e e f g a qkc` | 1 | 17 | 保留 |
| `，。、„""«»１»` | 1 | 12 | 保留 |
| `Do you need a cup of coffee?` | 1 | 25 | 过滤 |

## 输出示例

**命令行输出：**
```
[OK] Average line length filtering completed!
   Min length: 10
   Max length: 20
   Original documents: 6
   Filtered documents: 2
   Removed documents: 4
   Input file: ./input.json
   Output file: ./output.json
```

**输出JSON格式：**
```json
[
  {"text": "过滤后保留的文本1"},
  {"text": "过滤后保留的文本2"}
]
```

## 环境要求

**安装依赖：**
本SKILL使用依赖 data_juicer，请在调用前安装好python环境并安装data_juicer：
```bash
pip install py-data-juicer
```

## 注意事项

1. **平均行长度计算**：`总字符数 / 行数`
2. **默认值**：`max_len` 默认无限制
3. **过滤逻辑**：只保留平均行长度在 [min_len, max_len] 范围内的样本
4. **适用场景**：清理过短/过长文本行、过滤格式不规范文本
