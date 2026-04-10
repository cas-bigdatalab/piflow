# Parquet格式化器示例
# 输入文件格式:
# Parquet是一种列式存储格式，通常由pandas或huggingface datasets保存
#
# 使用说明:
# 1. 假设有一个 data.parquet 文件，包含 text 和 label 列
#
# 2. 加载并转换为 JSONL:
#    python scripts/run_parquet_formatter.py \
#      --input_path data.parquet \
#      --output_path output.jsonl \
#      --text_keys text
#
# 3. 输出结果:
#    {"text": "Sample text 1", "label": "positive"}
#    {"text": "Sample text 2", "label": "negative"}