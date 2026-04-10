import argparse
import json
import os

from data_juicer.format.mixture_formatter import MixtureFormatter


def run_mixture_formatter(dataset_path: str,
                          output_path: str,
                          suffixes: list = None,
                          text_keys: list = None,
                          add_suffix: bool = False,
                          max_samples: int = None,
                          num_proc: int = 1):
    """
    运行混合格式化算子

    :param dataset_path: 数据集路径，支持带权重格式
    :param output_path: 输出JSONL文件路径
    :param suffixes: 目标后缀列表
    :param text_keys: 文本字段名列表
    :param add_suffix: 是否添加文件后缀信息
    :param max_samples: 最大样本数
    :param num_proc: 并行进程数
    """
    # 处理默认参数
    if text_keys is None:
        text_keys = ['text']

    # 初始化格式化器
    formatter = MixtureFormatter(
        dataset_path=dataset_path,
        suffixes=suffixes,
        text_keys=text_keys,
        add_suffix=add_suffix,
        max_samples=max_samples
    )

    # 加载数据集
    dataset = formatter.load_dataset(num_proc=num_proc)

    # 保存为 JSONL 格式
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset.to_list():
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 混合数据集共 {len(dataset)} 条数据")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='混合格式化器 - 混合多个数据集'
    )
    parser.add_argument('--dataset_path', type=str, required=True,
                        help='数据集路径，支持带权重格式，如 "0.5 ds1.jsonl 0.5 ds2.jsonl"')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出JSONL文件路径')
    parser.add_argument('--suffixes', type=str, action='append', default=None,
                        help='目标后缀')
    parser.add_argument('--text_keys', type=str, action='append', default=None,
                        help='文本字段名 (默认: text)')
    parser.add_argument('--add_suffix', action='store_true',
                        help='是否添加文件后缀信息')
    parser.add_argument('--max_samples', type=int, default=None,
                        help='最大样本数')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_mixture_formatter(
        dataset_path=args.dataset_path,
        output_path=args.output_path,
        suffixes=args.suffixes,
        text_keys=args.text_keys,
        add_suffix=args.add_suffix,
        max_samples=args.max_samples,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()