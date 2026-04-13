# 远程格式化器示例
# 使用说明:
# 1. 加载HuggingFace公开数据集
#    python scripts/run_remote_formatter.py \
#      --dataset_path "rotten_tomatoes" \
#      --output_path output.jsonl
#
# 2. 指定文本字段和数据集划分
#    python scripts/run_remote_formatter.py \
#      --dataset_path "yelp_review_full" \
#      --output_path output.jsonl \
#      --text_keys text \
#      --split train
#
# 3. 加载私有数据集（需先登录）
#    huggingface-cli login
#    python scripts/run_remote_formatter.py \
#      --dataset_path "private_user/private_dataset" \
#      --output_path output.jsonl