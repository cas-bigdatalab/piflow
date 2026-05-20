---
name: chinese_convert_mapper
description: |
  在繁体中文、简体中文和日语汉字之间转换中文。当用户提到中文繁简转换、中文转换、简体转繁体、繁体转简体、中日文转换等需求时使用此skill。
  即使用户没有明确说出"转换"，只要任务涉及中文繁简转换或中日文转换，就应该使用此skill。

input_params:
  - name: input_path
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

  - name: mode
    type: string
    required: false
    default: s2t
    description: 转换模式，如 s2t、t2s、s2tw、t2jp 等

output_params:
  - name: output
    type: json_file
    description: 转换后的JSON文件，包含转换后的text字段
---

# Chinese Convert Mapper

在繁体中文、简体中文和日语汉字之间转换中文。

本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用同以下指令进行安装：
```
pip install py-data-juicer
```

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入JSON文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |
| mode | string | 否 | s2t | 转换模式 |

### 支持的转换模式

| 模式 | 说明 |
|------|------|
| s2t | 简体中文 → 繁体中文 |
| t2s | 繁体中文 → 简体中文 |
| s2tw | 简体中文 → 繁体中文（台湾标准） |
| tw2s | 繁体中文（台湾标准）→ 简体中文 |
| s2hk | 简体中文 → 繁体中文（香港变体） |
| hk2s | 繁体中文（香港变体）→ 简体中文 |
| s2twp | 简体中文 → 繁体中文（台湾习惯用语） |
| tw2sp | 繁体中文（台湾习惯用语）→ 简体中文 |
| t2tw | 繁体中文 → 繁体中文（台湾标准） |
| tw2t | 繁体中文（台湾标准）→ 繁体中文 |
| hk2t | 繁体中文（香港变体）→ 繁体中文 |
| t2hk | 繁体中文 → 繁体中文（香港变体） |
| t2jp | 繁体中文（传统字形）→ 日语新字体 |
| jp2t | 日语新字体 → 繁体中文（传统字形） |

## 使用方法

```bash
python scripts/run_chinese_convert_mapper.py --input_path <input_path> --output_path <output_path> [--mode <mode>]
```

## 实现原理

参照测试代码 test_chinese_convert_mapper.py 中的 `_run_chinese_convert` 函数：

```python
# 1. 初始化算子
op = ChineseConvertMapper(mode='s2t')

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "这是几个简体字"},
  {"text": "這是幾個繁體字"}
]
```

### 输出格式 (JSON数组)

```json
[
  {"text": "這是幾個簡體字"},
  {"text": "這是幾個繁體字"}
]
```

## 示例

### 示例1：简体转繁体（默认）

```bash
python scripts/run_chinese_convert_mapper.py --input_path example_input.json --output_path output.json
```

### 示例2：繁体转简体

```bash
python scripts/run_chinese_convert_mapper.py --input_path example_input.json --output_path output.json --mode t2s
```

### 示例3：简体转台湾繁体

```bash
python scripts/run_chinese_convert_mapper.py --input_path example_input.json --output_path output.json --mode s2tw
```

## 注意事项

- 默认模式为 s2t（简体转繁体）
- 转换只影响 text 字段，其他字段保持不变
- 不在转换范围内的字符（如数字、英文、标点符号）保持原样
