import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.grouper.naive_grouper import NaiveGrouper


def run_naive_grouper(input_path: str, output_path: str):
    """
    Naive Grouper - 将所有样本分组为一批样品

    参照测试代码 test_naive_grouper.py 中的 _run_helper 函数实现：
    1. Dataset.from_list(samples) - 将输入列表转换为Dataset
    2. op.run(dataset) - 执行合并操作
    3. 将结果保存为JSON文件

    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
    """
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 将输入列表转换为Dataset
    dataset = Dataset.from_list(samples)

    # 初始化算子并执行合并（无参数）
    op = NaiveGrouper()
    batched_dataset = op.run(dataset)

    # 将结果转换为列表并保存
    batched_list = [dict(sample) for sample in batched_dataset]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batched_list, f, ensure_ascii=False, indent=2)

    print(f"处理完成：{len(samples)} 条样本 -> {len(batched_list)} 个批次")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Naive Grouper - 将所有样本合并为一批")
    parser.add_argument(
        "--input_path", type=str, required=True, help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="输出JSON文件路径"
    )

    args = parser.parse_args()
    run_naive_grouper(args.input_path, args.output_path)
