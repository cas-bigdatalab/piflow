# 混合格式化器示例
# 使用说明:
# 1. 准备两个数据集文件 (dataset1.jsonl 和 dataset2.jsonl)
#
# 2. 混合两个数据集，等权重
#    python scripts/run_mixture_formatter.py \
#      --dataset_path "dataset1.jsonl dataset2.jsonl" \
#      --output_path output.jsonl
#
# 3. 带权重的混合 (70% 来自 dataset1, 30% 来自 dataset2)
#    python scripts/run_mixture_formatter.py \
#      --dataset_path "0.7 dataset1.jsonl 0.3 dataset2.jsonl" \
#      --output_path output.jsonl
#
# 4. 限制最大样本数为 10000
#    python scripts/run_mixture_formatter.py \
#      --dataset_path "dataset1.jsonl dataset2.jsonl" \
#      --output_path output.jsonl \
#      --max_samples 10000