---
name: naive_grouper
description: |
  将所有样本分组为一批样品。当用户提到样本合并、合并所有样本、一批分组、全部聚合等需求时使用此skill。
  即使用户没有明确说出"合并"，只要任务涉及将多个样本合并为单个批次，就应该使用此skill。

name_zh: 将所有样本分组为一批样品算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

output_params:
  - name: output
    type: json_file
    description: 合并后的JSON文件，所有样本合并为一个批次
tag: 增强

---

# Naive Grouper

将所有样本分组为一批样品。

本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用同以下指令进行安装：
```
pip install py-data-juicer
```

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入JSON文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |

## 使用方法

```bash
python scripts/run_naive_grouper.py --input_path <input_path> --output_path <output_path>
```

## 实现原理

参照测试代码 test_naive_grouper.py 中的 `_run_helper` 函数：

```python
# 1. 将输入列表转换为Dataset
dataset = Dataset.from_list(samples)

# 2. 初始化算子并执行（无需参数）
op = NaiveGrouper()
new_dataset = op.run(dataset)
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "Sample 1"},
  {"text": "Sample 2"},
  {"text": "Sample 3"}
]
```

### 输出格式 (JSON数组，只有一个元素)

```json
[
  {"text": ["Sample 1", "Sample 2", "Sample 3"]}
]
```

## 示例

执行：
```bash
python scripts/run_naive_grouper.py --input_path example_input.json --output_path output.json
```

## 注意事项

- 此算子无需额外参数
- 所有输入样本会被合并为一个批次
- 合并后的字段值为数组形式
