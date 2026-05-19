---
name: flagged_words_filter
description: |
  敏感词过滤器。过滤文本中包含敏感词/标记词比例超过指定阈值的样本。
  当用户提到敏感词过滤、脏词过滤、违禁词过滤、内容审核、敏感词检测等需求时使用此skill。
  即使用户没有明确说出"敏感词"，只要任务涉及过滤包含特定敏感词的文本内容，
  就应该使用此skill。

input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: lang
    type: string
    required: false
    default: en
    description: 语言（en/zh/all）

  - name: max_ratio
    type: float
    required: false
    default: 0.045
    description: 最大敏感词比例

  - name: tokenization
    type: bool
    required: false
    default: false
    description: 是否使用模型分词

  - name: use_words_aug
    type: bool
    required: false
    default: false
    description: 是否使用词语增强

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

output_params:
  - name: output
    type: json_file
    description: 过滤敏感词后的JSON文件
---

# Flagged Words Filter 敏感词过滤 Skill

## 功能概述

本skill根据文本中敏感词/标记词的比例进行过滤，只保留敏感词比例低于指定阈值的样本。
支持多语言（英文、中文等），常用于内容审核、数据清洗等场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 敏感词过滤
- 脏词过滤
- 违禁词过滤
- 内容审核
- 敏感词检测
- 不良内容过滤
- 清洗违规文本

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--lang` | 语言 | `en` |
| `--max_ratio` | 最大敏感词比例 | `0.045` |
| `--tokenization` | 是否使用模型分词 | `False` |
| `--use_words_aug` | 是否使用词语增强 | `False` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {"text": "正常文本内容"},
  {"text": "包含敏感词的文本"},
  {"text": "另一段正常文本"}
]
```

## 使用方法

### 英文敏感词过滤（默认）
```bash
python scripts/run_flagged_words_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 中文敏感词过滤
```bash
python scripts/run_flagged_words_filter.py \
  --input ./input.json \
  --output ./output.json \
  --lang zh
```

### 自定义最大敏感词比例
```bash
python scripts/run_flagged_words_filter.py \
  --input ./input.json \
  --output ./output.json \
  --max_ratio 0.03
```

### 使用分词模型（更精确）
```bash
python scripts/run_flagged_words_filter.py \
  --input ./input.json \
  --output ./output.json \
  --tokenization True
```

## 支持的语言

| 语言代码 | 说明 |
|----------|------|
| `en` | 英语（默认） |
| `zh` | 中文 |
| `all` | 所有语言合并 |

## 输出示例

**命令行输出：**
```
[OK] Flagged words filtering completed!
   Language: en
   Max ratio: 0.045
   Tokenization: False
   Original documents: 5
   Filtered documents: 3
   Removed documents: 2
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

1. **敏感词列表**：使用 data_juicer 内置的敏感词库
2. **过滤逻辑**：只保留敏感词比例 <= max_ratio 的样本
3. **语言支持**：建议根据文本语言选择合适的 --lang 参数
4. **适用场景**：内容审核、数据清洗、违规内容过滤
