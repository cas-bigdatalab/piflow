---
name: clean_copyright_mapper
description: |
  清理版权注释开头的文本样本。当用户提到清理版权、删除版权注释、清理代码注释、去除版权信息等需求时使用此skill。
  即使用户没有明确说出"版权"，只要任务涉及清理文本开头的注释或版权信息，就应该使用此skill。

name_zh: 清理版权注释开头的文本样本算子
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
    description: 清理版权注释后的JSON文件
tag: 标准化

---

# Clean Copyright Mapper

清理文本开头的版权注释，包括多行注释和单行注释。

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
python scripts/run_clean_copyright_mapper.py --input_path <input_path> --output_path <output_path>
```

## 实现原理

参照测试代码 test_clean_copyright_mapper.py 中的 `_run_clean_copyright` 函数：

```python
# 1. 初始化算子（无参数）
op = CleanCopyrightMapper()

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## 清理规则

1. **多行注释清理**：清理包含 "copyright" 关键词的多行注释（/* ... */）
2. **单行注释清理**：清理文本开头以 `//`、`#`、`--` 开头的行

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "/* 多行注释\n版权信息 */\n正文内容"},
  {"text": "//单行注释\n正文内容"}
]
```

### 输出格式 (JSON数组)

```json
[
  {"text": "\n正文内容"},
  {"text": "正文内容"}
]
```

## 示例

### 示例：清理版权注释

输入：
```json
[
  {"text": "/* copyright注释 */\n这是正文"},
  {"text": "//这是一行注释\n这是正文"}
]
```

执行：
```bash
python scripts/run_clean_copyright_mapper.py --input_path example_input.json --output_path output.json
```

输出：
```json
[
  {"text": "\n这是正文"},
  {"text": "这是正文"}
]
```

## 注意事项

- 此算子无额外参数
- 只清理文本开头的注释，不会影响正文中的注释
- 多行注释必须包含 "copyright" 关键词才会被清理
