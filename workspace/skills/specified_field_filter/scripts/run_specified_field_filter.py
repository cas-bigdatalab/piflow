import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.specified_field_filter import SpecifiedFieldFilter


def run_specified_field_filter(input_path: str, output_path: str,
                               field_key: str,
                               target_value: list,
                               num_proc: int = 1):
    """
    运行指定字段过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param field_key: 字段路径
    :param target_value: 目标值列表
    :param num_proc: 并行进程数
    """
    # 读取输入数据
    if input_path.endswith('.jsonl'):
        ds_list = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    ds_list.append(json.loads(line))
    elif input_path.endswith('.json'):
        with open(input_path, 'r', encoding='utf-8') as f:
            ds_list = json.load(f)
    else:
        raise ValueError(f"Unsupported input file format: {input_path}")

    # 创建数据集
    dataset = Dataset.from_list(ds_list)

    # 初始化算子
    op = SpecifiedFieldFilter(
        field_key=field_key,
        target_value=target_value
    )

    # 处理数据（不需要计算统计信息）
    dataset = dataset.map(op.compute_stats)
    dataset = dataset.filter(op.process, num_proc=num_proc)

    # 保存结果
    res_list = dataset.to_list()
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in res_list:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 输入 {len(ds_list)} 条 -> 输出 {len(res_list)} 条")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='指定字段过滤器 - 根据字段值进行过滤'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--field_key', type=str, required=True,
                        help='字段路径，支持嵌套，用点号分隔，如 meta.suffix')
    parser.add_argument('--target_value', type=str, action='append', required=True,
                        help='目标值，可重复指定多个值')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_specified_field_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        field_key=args.field_key,
        target_value=args.target_value,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()