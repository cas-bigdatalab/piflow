---
name: clean_ip_mapper
description: |
  清除文本示例中的IPv4和IPv6地址。当用户提到清理IP、删除IP地址、去除IP、清理网络地址等需求时使用此skill。
  即使用户没有明确说出"IP"，只要任务涉及从文本中删除或替换IP地址，就应该使用此skill。

name_zh: 清除文本示例中的IPv4和IPv6地址算子
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
  - name: output
    type: json_file
    description: 清理IP地址后的JSON文件
tag: 标准化

---

# Clean IP Mapper

清除文本中的IPv4和IPv6地址。

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
python scripts/run_clean_ip_mapper.py --input_path <input_path> --output_path <output_path> [--repl <replacement>]
```

## 实现原理

参照测试代码 test_clean_ip_mapper.py 中的 `_run_clean_ip` 函数：

```python
# 1. 初始化算子
op = CleanIpMapper()  # 删除IP
# 或
op = CleanIpMapper(repl='<IP>')  # 替换为指定字符串

# 2. 将数据转为Dataset，使用 op.run(dataset) 处理
dataset = Dataset.from_list(samples)
result_dataset = op.run(dataset)
```

## 输入输出格式

### 输入格式 (JSON数组)

```json
[
  {"text": "服务器IP：192.168.1.1"},
  {"text": "IPv6地址：2001:0db8:85a3"}
]
```

### 输出格式 (JSON数组)

```json
[
  {"text": "服务器IP："},
  {"text": "IPv6地址："}
]
```

## 示例

### 示例1：删除IP地址（默认）

```bash
python scripts/run_clean_ip_mapper.py --input_path example_input.json --output_path output.json
```

### 示例2：替换为占位符

```bash
python scripts/run_clean_ip_mapper.py --input_path example_input.json --output_path output.json --repl "<IP>"
```

## 注意事项

- 默认行为是删除IP地址
- 可以指定 `repl` 参数来替换为其他字符串
- 支持IPv4和IPv6地址的识别和清理
