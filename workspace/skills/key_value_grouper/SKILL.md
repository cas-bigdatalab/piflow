---
name: key_value_grouper
description: |
  根据给定键中的值将样本分组为批处理样本。当用户提到样本分组、按键值分组、批处理样本、按键聚合、分组聚合等需求时使用此skill。
  即使用户没有明确说出"分组"，只要任务涉及将多个样本按某个字段/键的值进行归类合并，就应该使用此skill。

name_zh: 根据给定键中的值将样本分组为批处理样本算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

  - name: group_by_keys
    type: string
    required: false
    default: text
    description: 分组键，逗号分隔，支持嵌套键如 "meta.language"

output_params:
  - name: output
    type: json_file
    description: 分组后的JSON文件，每组样本的字段值为数组
tag: 增强

---

# Key Value Grouper

根据给定键中的值将样本分组为批处理样本。

本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用同以下指令进行安装：
```
pip install py-data-juicer
```

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入JSON文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |
| group_by_keys | string | 否 | "text" | 分组键，逗号分隔，支持嵌套键如 "meta.language" |

## 使用方法

```bash
python scripts/run_key_value_grouper.py --input_path <input_path> --output_path <output_path> [--group_by_keys <keys>]
```

## 实现原理

参照测试代码中的 `_run_helper` 函数：

```python
# 1. 将输入列表转换为Dataset
dataset = Dataset.from_list(samples)

# 2. 初始化算子并执行
op = KeyValueGrouper(group_by_keys=['meta.language'])
new_dataset = op.run(dataset)

# 3. 遍历分组结果
for batched_sample in new_dataset:
    lang = batched_sample['meta'][0]['language']
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "Hello world", "meta": {"language": "en"}},
  {"text": "Hello world", "meta": {"language": "en"}},
  {"text": "欢迎来到阿里巴巴！", "meta": {"language": "zh"}}
]
```

### 输出格式 (JSON数组，每个元素是一组样本)

```json
[
  {"text": ["Hello world", "Hello world"], "meta": [{"language": "en"}, {"language": "en"}]},
  {"text": ["欢迎来到阿里巴巴！"], "meta": [{"language": "zh"}]}
]
```

## 示例

### 示例1：按默认text字段分组

执行：
```bash
python scripts/run_key_value_grouper.py --input_path example_input.json --output_path output.json
```

### 示例2：按meta.language分组

执行：
```bash
python scripts/run_key_value_grouper.py --input_path example_input.json --output_path output.json --group_by_keys "meta.language"
```

## 注意事项

- 支持嵌套键，使用点号分隔（如 "meta.language"）
- 支持多键分组，逗号分隔（如 "meta.lang,meta.topic"）
- 相同键值的样本会被合并为一组，合并后的字段值为数组
