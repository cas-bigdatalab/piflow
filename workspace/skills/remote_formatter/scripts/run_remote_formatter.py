import argparse
import json
import os

from data_juicer.format.formatter import RemoteFormatter


def run_remote_formatter(dataset_path: str,
                        output_path: str,
                        text_keys: list = None,
                        split: str = 'train',
                        num_proc: int = 1):
    """
    运行远程格式化算子

    :param dataset_path: HuggingFace数据集路径
    :param output_path: 输出JSONL文件路径
    :param text_keys: 文本字段名列表
    :param split: 数据集划分
    :param num_proc: 并行进程数
    """
    # 处理默认参数
    if text_keys is None:
        text_keys = ['text']

    # 初始化格式化器
    formatter = RemoteFormatter(
        dataset_path=dataset_path,
        text_keys=text_keys,
        split=split
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
        description='远程格式化器 - 从HuggingFace Hub加载数据集'
    )
    parser.add_argument('--dataset_path', type=str, required=True,
                        help='HuggingFace数据集路径')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出JSONL文件路径')
    parser.add_argument('--text_keys', type=str, action='append', default=None,
                        help='文本字段名 (默认: text)')
    parser.add_argument('--split', type=str, default='train',
                        help='数据集划分 (默认: train)')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_remote_formatter(
        dataset_path=args.dataset_path,
        output_path=args.output_path,
        text_keys=args.text_keys,
        split=args.split,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()