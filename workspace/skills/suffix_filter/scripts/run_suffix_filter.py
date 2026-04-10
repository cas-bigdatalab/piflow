import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.suffix_filter import SuffixFilter


def run_suffix_filter(input_path: str, output_path: str,
                    suffixes: list = None,
                    num_proc: int = 1):
    """
    运行后缀过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param suffixes: 目标后缀列表
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

    # 处理后缀参数
    suffixes_param = suffixes if suffixes else []

    # 初始化算子
    op = SuffixFilter(suffixes=suffixes_param)

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
        description='后缀过滤器 - 根据文件后缀进行过滤'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--suffixes', type=str, action='append', default=None,
                        help='目标后缀，如 .txt, .pdf, .docx，可重复指定多个')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_suffix_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        suffixes=args.suffixes,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()