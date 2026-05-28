---
name: clean_links_mapper
description: |
  清理文本中的链接（HTTP/HTTPS/FTP）。当用户提到清理链接、删除URL、去除超链接、清理网页链接等需求时使用此skill。
  即使用户没有明确说出"链接"，只要任务涉及从文本中删除或替换URL链接，就应该使用此skill。

name_zh: 清理文本中的链接（HTTP/HTTPS/FTP）算子
input_params:
  - name: input_path
    type: string
    required: true
    description: 输入JSON文件路径

  - name: output_path
    type: string
    required: true
    description: 输出JSON文件路径

  - name: repl
    type: string
    required: false
    default: ""
    description: 替换字符串（默认为空，即删除）

output_params:
  - name: output_path
    type: json_file
    description: 清理链接后的JSON文件
tag: 标准化

---

# Clean Links Mapper

清理文本中的HTTP、HTTPS、FTP链接。

本SKILL使用依赖data_juicer，请在调用前安装好python环境并安装data_juicer，你可用同以下指令进行安装：
```
pip install py-data-juicer
```

## 核心参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| input_path | string | 是 | - | 输入JSON文件路径 |
| output_path | string | 是 | - | 输出JSON文件路径 |
| repl | string | 否 | 空字符串 | 替换字符串（默认为删除） |

## 使用方法

```bash
python scripts/run_clean_links_mapper.py --input_path <input_path> --output_path <output_path> [--repl <replacement>]
```

## 实现原理

参照测试代码 test_clean_links_mapper.py 中的 `_run_clean_links` 函数：

```python
# 1. 初始化算子
op = CleanLinksMapper()  # 删除链接
# 或
op = CleanLinksMapper(repl='<LINKS>')  # 替换为指定字符串

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "访问 https://www.example.com 了解更多信息"},
  {"text": "FTP服务器：ftp://ftp.example.com"}
]
```

### 输出格式 (JSON数组)

```json
[
  {"text": "访问  了解更多信息"},
  {"text": "FTP服务器："}
]
```

## 示例

### 示例1：删除链接（默认）

```bash
python scripts/run_clean_links_mapper.py --input_path example_input.json --output_path output.json
```

### 示例2：替换为占位符

```bash
python scripts/run_clean_links_mapper.py --input_path example_input.json --output_path output.json --repl "<LINKS>"
```

## 注意事项

- 默认行为是删除链接
- 可以指定 `repl` 参数来替换为其他字符串
- 支持HTTP、HTTPS、FTP协议的链接
- 不区分大小写（HTTP、Http、HTTP都会被识别）
