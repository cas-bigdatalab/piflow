---
name: character_repetition_filter
description: |
  字符重复比例过滤器。过滤文本中字符级n-gram重复比例不在指定范围内的样本。
  当用户提到字符重复、重复比例过滤、文本重复过滤、清理重复内容等需求时使用此skill。
  即使用户没有明确说出"字符重复"，只要任务涉及根据文本中字符重复的程度来筛选数据，
  就应该使用此skill。

name_zh: 字符重复比例过滤器算子
input_params:
  - name: input
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output
    type: string
    required: true
    description: 输出JSON文件路径

  - name: rep_len
    type: int
    required: false
    default: 10
    description: 字符级n-gram重复长度

  - name: min_ratio
    type: float
    required: false
    default: 0.0
    description: 最小重复比例

  - name: max_ratio
    type: float
    required: false
    default: 0.5
    description: 最大重复比例

  - name: text_key
    type: string
    required: false
    default: text
    description: 文本字段的键名

output_params:
  - name: output
    type: json_file
    description: 过滤后的JSON文件，包含字符重复比例在指定范围内的样本
tag: 过滤与筛选

---

# Character Repetition Filter 字符重复比例过滤 Skill

## 功能概述

本skill根据文本中字符级n-gram的重复比例进行过滤，只保留重复比例在指定范围内的样本。
常用于过滤过度重复的文本、清理模板生成的低质量文本等场景。

## 触发条件

当用户请求以下任务时，应使用此skill：
- 字符重复过滤
- 重复比例筛选
- 文本重复过滤
- 清理重复内容
- 过滤模板文本
- 检测重复文本

## 核心参数说明

### 必需参数
| 参数 | 说明 |
|------|------|
| `--input` | 输入JSON文件路径 |
| `--output` | 输出JSON文件路径 |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--rep_len` | 字符级n-gram重复长度 | `10` |
| `--min_ratio` | 最小重复比例 | `0.0` |
| `--max_ratio` | 最大重复比例 | `0.5` |
| `--text_key` | 文本字段的键名 | `text` |

## 输入文件格式

```json
[
  {"text": "正常文本内容"},
  {"text": "过度重复的文本aaaaaaa..."},
  {"text": "另一段正常文本"}
]
```

## 使用方法

### 默认参数过滤（rep_len=10, min_ratio=0.0, max_ratio=0.5）
```bash
python scripts/run_character_repetition_filter.py \
  --input ./input.json \
  --output ./output.json
```

### 自定义重复比例范围
```bash
python scripts/run_character_repetition_filter.py \
  --input ./input.json \
  --output ./output.json \
  --min_ratio 0.0 \
  --max_ratio 0.4
```

### 自定义n-gram长度
```bash
python scripts/run_character_repetition_filter.py \
  --input ./input.json \
  --output ./output.json \
  --rep_len 5
```

## 过滤示例

| 文本 | 重复比例 | 过滤结果 (0.0-0.4) |
|------|----------|---------------------|
| `Today is Sund Sund Sund Sund Sund Sunda...` | 高 | 过滤 |
| `a v s e c s f e f g a a a a a a a a a a` | 高 | 过滤 |
| `，。、„""«»１»...` | 低 | 保留 |
| `中文也是一个字算一个长度` | 低 | 保留 |

## 输出示例

**命令行输出：**
```
[OK] Character repetition filtering completed!
   Rep length: 10
   Min ratio: 0.0
   Max ratio: 0.4
   Original documents: 4
   Filtered documents: 2
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

1. **重复比例计算**：基于字符级n-gram的频率分布计算
2. **默认值**：保留重复比例在0.0-0.5之间的样本
3. **过滤逻辑**：只保留重复比例在 [min_ratio, max_ratio] 范围内的样本
4. **适用场景**：清理模板文本、过滤重复内容、检测低质量文本
