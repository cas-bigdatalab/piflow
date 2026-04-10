# TSV格式化器示例
# 输入文件格式 (TSV - Tab-Separated Values):
# text	label
# "First sample text"	positive
# "Second sample text"	negative
# "Third sample text"	neutral

# 使用说明:
# 1. 将上述内容保存为 TSV 文件 (data.tsv)
# 2. 使用脚本加载并转换为 JSONL 格式:
#    python scripts/run_tsv_formatter.py --input_path data.tsv --output_path output.jsonl --text_keys text
# 3. 输出结果:
#    {"text": "First sample text", "label": "positive"}
#    {"text": "Second sample text", "label": "negative"}
#    {"text": "Third sample text", "label": "neutral"}