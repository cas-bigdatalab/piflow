# 空数据格式化器示例
# 使用说明:
# 1. 创建10条空数据，无字段
#    python scripts/run_empty_formatter.py --output_path output.jsonl --length 10
#
# 2. 创建5条空数据，指定字段
#    python scripts/run_empty_formatter.py --output_path output.jsonl --length 5 --feature_keys text --feature_keys label
#
# 3. 输出示例:
#    {"text": null, "label": null}
#    {"text": null, "label": null}