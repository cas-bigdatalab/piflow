import argparse
import json
from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.grouper.key_value_grouper import KeyValueGrouper


def run_key_value_grouper(input_path: str, output_path: str, group_by_keys: str = "text"):
    """
    Key Value Grouper - 根据给定键中的值将样本分组为批处理样本
    
    参照测试代码 test_key_value_grouper.py 中的 _run_helper 函数实现：
    1. Dataset.from_list(samples) - 将输入列表转换为Dataset
    2. op.run(dataset) - 执行分组操作
    3. 遍历 new_dataset 获取分组结果
    
    参数:
        input_path: 输入JSON文件路径
        output_path: 输出JSON文件路径
        group_by_keys: 分组键，逗号分隔，默认"text"
    """
    # 解析分组键列表
    group_by_keys_list = [k.strip() for k in group_by_keys.split(",")]
    
    # 读取输入文件
    with open(input_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    
    # 将输入列表转换为Dataset
    dataset = Dataset.from_list(samples)
    
    # 初始化算子并执行分组
    op = KeyValueGrouper(group_by_keys=group_by_keys_list)
    batched_dataset = op.run(dataset)
    
    # 将结果转换为列表并保存
    batched_list = [dict(sample) for sample in batched_dataset]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batched_list, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成：{len(samples)} 条样本 -> {len(batched_list)} 个批次")
    print(f"输出文件：{output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Key Value Grouper - 按键值分组样本")
    parser.add_argument("--input_path", type=str, required=True, help="输入JSON文件路径")
    parser.add_argument("--output_path", type=str, required=True, help="输出JSON文件路径")
    parser.add_argument("--group_by_keys", type=str, default="text", help="分组键，逗号分隔")
    
    args = parser.parse_args()
    run_key_value_grouper(args.input_path, args.output_path, args.group_by_keys)
