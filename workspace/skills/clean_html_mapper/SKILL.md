---
name: clean_html_mapper
description: |
  清理文本示例中的HTML代码。当用户提到清理HTML、去除HTML标签、HTML转文本、提取网页文本等需求时使用此skill。
  即使用户没有明确说出"HTML"，只要任务涉及从HTML代码中提取纯文本，就应该使用此skill。

name_zh: 清理文本示例中的HTML代码算子
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
  - name: output_path
    type: json_file
    description: 清理HTML后的JSON文件
tag: 标准化

---

# Clean HTML Mapper

清理文本中的HTML代码，提取纯文本内容。

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
python scripts/run_clean_html_mapper.py --input_path <input_path> --output_path <output_path>
```

## 实现原理

参照测试代码 test_clean_html_mapper.py 中的 `_run_helper` 函数：

```python
# 1. 初始化算子（无参数）
op = CleanHtmlMapper()

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## HTML清理规则

1. `<li>` 和 `<ol>` 标签转换为 `*` 列表格式
2. 使用 selectolax 解析器提取纯文本
3. 移除所有HTML标签
4. 保留文本内容和换行符

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "<p>这是段落</p>"},
  {"text": "<li>列表项1</li><li>列表项2</li>"}
]
```

### 输出格式 (JSON数组)

```json
[
  {"text": "这是段落"},
  {"text": "\n*列表项1\n*列表项2"}
]
```

## 示例

### 示例：清理HTML

输入：
```json
[
  {"text": "<p>这是测试</p>"},
  {"text": "<div><p>Hello World</p></div>"}
]
```

执行：
```bash
python scripts/run_clean_html_mapper.py --input_path example_input.json --output_path output.json
```

输出：
```json
[
  {"text": "这是测试"},
  {"text": "Hello World"}
]
```

## 注意事项

- 此算子无额外参数
- 会自动处理列表标签（`<li>`, `<ol>`）转换为 `*` 格式
- 不符合HTML格式的标签内容也会被尝试清理
