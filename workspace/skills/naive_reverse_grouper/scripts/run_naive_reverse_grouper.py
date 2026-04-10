import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.grouper.naive_reverse_grouper import NaiveReverseGrouper


def run_naive_reverse_grouper(
    input_path: str, output_path: str, export_path: str = None
):
    """
    Naive Reverse Grouper - 将批处理的样本拆分为独立样本

    参照测试代码 test_naive_reverse_grouper.py 中的 _run_helper 函数实现：
    1. Dataset.from_list(samples) - 将批次化样本转换为Dataset
    2. op.run(dataset) - 执行拆分操作
    3. 将结果保存为JSON文件

    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        export_path: 可选，导出批次元数据到JSONL文件
    """
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    # 将批次化样本列表转换为Dataset
    dataset = Dataset.from_list(samples)

    # 初始化算子并执行拆分
    if export_path:
        op = NaiveReverseGrouper(export_path=export_path)
    else:
        op = NaiveReverseGrouper()
    ungrouped_dataset = op.run(dataset)

    # 将结果转换为列表并保存
    ungrouped_list = [dict(sample) for sample in ungrouped_dataset]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ungrouped_list, f, ensure_ascii=False, indent=2)

    print(f"处理完成：{len(samples)} 批次 -> {len(ungrouped_list)} 条样本")
    print(f"输出文件：{output_path}")

    if export_path:
        print(f"批次元数据已导出：{export_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Naive Reverse Grouper - 将批处理样本拆分为独立样本"
    )
    parser.add_argument(
        "--input_path", type=str, required=True, help="输入JSON文件路径"
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="输出JSON文件路径"
    )
    parser.add_argument(
        "--export_path", type=str, default=None, help="可选，导出批次元数据到JSONL文件"
    )

    args = parser.parse_args()
    run_naive_reverse_grouper(args.input_path, args.output_path, args.export_path)
