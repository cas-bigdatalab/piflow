---
name: scientific_formula_normalizer
description: |
  科学公式格式规整工具。读取包含数理公式的 UTF-8 文本，统一公式中的上下标标识、基础运算符、全角或异体括号、公式内部空白和不可见干扰字符，并输出规整后的文本文件。
  当用户提到科学公式规整、数学表达式标准化、上下标统一、运算符号统一、公式括号规范化等需求时使用此 skill。
  即使用户没有明确说出"scientific_formula_normalizer"，只要任务涉及数理、物理或统计科研文本内嵌公式的符号和排版规整，就应该使用此 skill。
  适用范围按用户给定目标和当前 skill 的实际能力描述；不要替用户额外拆分或取舍需求。
name_zh: 科学公式格式规整算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 包含数理公式的 UTF-8 文本文件路径
  - name: output_path
    type: string
    required: true
    description: 规整后文本文件的输出路径
output_params:
  - name: output_path
    type: txt_file
    description: 科学公式格式规整后的文本文件
tag: 数据清洗
publisher: COMMUNITY
---

# scientific_formula_normalizer 科学公式格式规整算子

## 功能概述

读取 UTF-8 纯文本，将科研语料中内嵌的基础数理公式规整为统一的 ASCII 文本表示。算子将 Unicode 上标和下标转换为带花括号的 `^{...}` 与 `_{...}`，统一常见基础运算符及全角或异体括号，并清理公式内部冗余空白和不可见干扰字符。

## 触发条件

- 科学公式格式规整
- 数学表达式标准化
- 上下标符号统一
- 运算符号、括号格式规范化
- 数理科研文本预处理

## 处理逻辑

1. 删除零宽空格、字节顺序标记等不可见干扰字符，并将不换行空格转换为空格。
2. 将 Unicode 上标和下标字符分别转换为 `^{...}` 和 `_{...}` 文本标记；相邻同类上下标会合并为一个花括号组。
3. 将加、减、乘、除、等号等常见全角或异体运算符转换为 ASCII 表示。
4. 将全角和常见异体圆括号、方括号、花括号转换为对应的 ASCII 层级括号，保留原有括号层级和内容。
5. 先识别由变量、数值、上下标、括号和运算符组成的基础公式片段，再只在片段内部删除无意义空白；同一行的普通英文词间空格和正文破折号保持不变。

## 使用方法

```bash
python scripts/scientific_formula_normalizer.py \
  --input_path {input_path} \
  --output_path {output_path}
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--input_path` | 是 | 包含数理公式的 UTF-8 文本文件路径。 |
| `--output_path` | 是 | 规整后文本文件的输出路径；缺失的父目录会自动创建。 |

## 输出示例

```text
输入: E ＝ m c²，x₁ ＋ （ y ÷ 2 ）
输出: E=mc^{2}，x_{1}+(y/2)
```

## 注意事项

- 本算子识别由单字母拉丁/希腊变量、数值、上下标、括号和基础运算符组成的公式片段；不把普通英文单词视为公式变量。
- 本算子仅做符号和格式级规整，不执行公式语义解析、等式求解、单位换算或括号配平。
- 仅处理 UTF-8 文本文件；原始换行结构保持不变。
- 乘号 `·` 会规整为 `*`，适用于将其用作乘法符号的基础数理表达式。

## 脚本说明

入口脚本 `scripts/scientific_formula_normalizer.py` 仅使用 Python 标准库完成文本读写和正则规则处理。
