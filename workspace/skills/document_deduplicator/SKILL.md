---
name: document_deduplicator
description: 对CSV数据集按文本字段进行文档级去重，基于文本MD5哈希过滤重复样本。
allowed-tools:
  - process1
---

# document_deduplicator

对CSV数据集进行文档级去重。

适用场景：

- 清洗训练数据
- 过滤重复文本
- 数据集预处理

参数：

- `input_file` 输入CSV文件路径
- `output_file` 输出去重后的CSV文件
- `duplicate_file` 重复样本记录文件
- `text_key` 文本字段名称（默认 text）
- `lowercase` 是否转为小写
- `ignore_non_character` 是否忽略非字母字符
- `show_num` 记录重复样本数量

规则：

- 如果 `output_file` 未指定，则自动生成 `_deduplicated.csv`
- 去重基于文本MD5哈希