import argparse
import json
import os

from data_juicer.format.formatter import LocalFormatter


def run_local_formatter(input_path: str,
                       output_path: str,
                       suffixes: list = None,
                       text_keys: list = None,
                       add_suffix: bool = False,
                       num_proc: int = 1):
    """
    运行本地格式化器

    :param input_path: 输入数据集文件或目录路径
    :param output_path: 输出JSONL文件路径
    :param suffixes: 目标后缀列表
    :param text_keys: 文本字段名列表
    :param add_suffix: 是否添加文件后缀信息
    :param num_proc: 并行进程数
    """
    # 处理默认参数
    if text_keys is None:
        text_keys = ['text']

    # 初始化格式化器
    formatter = LocalFormatter(
        dataset_path=input_path,
        type=None,
        suffixes=suffixes,
        text_keys=text_keys,
        add_suffix=add_suffix
    )

    # 加载数据集
    dataset = formatter.load_dataset(num_proc=num_proc)

    # 保存为 JSONL 格式
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in dataset.to_list():
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 共 {len(dataset)} 条数据")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='本地格式化器 - 从本地文件或目录加载数据集'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据集文件或目录路径')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出JSONL文件路径')
    parser.add_argument('--suffixes', type=str, action='append', default=None,
                        help='目标后缀，如 .json, .csv，可重复指定多个')
    parser.add_argument('--text_keys', type=str, action='append', default=None,
                        help='文本字段名 (默认: text)')
    parser.add_argument('--add_suffix', action='store_true',
                        help='是否添加文件后缀信息')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_local_formatter(
        input_path=args.input_path,
        output_path=args.output_path,
        suffixes=args.suffixes,
        text_keys=args.text_keys,
        add_suffix=args.add_suffix,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()