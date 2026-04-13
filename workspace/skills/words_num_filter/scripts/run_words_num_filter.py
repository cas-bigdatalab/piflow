import argparse
import json
import os
import sys

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.words_num_filter import WordsNumFilter
from data_juicer.utils.constant import Fields


def run_words_num_filter(input_path: str, output_path: str,
                   lang: str = 'en',
                   tokenization: bool = False,
                   min_num: int = 10,
                   max_num: int = sys.maxsize,
                   batch_size: int = 1,
                   num_proc: int = 1):
    """
    运行单词数量过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param lang: 语言代码
    :param tokenization: 是否使用分词模型
    :param min_num: 最小单词数量
    :param max_num: 最大单词数量
    :param batch_size: 批处理大小
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
    op = WordsNumFilter(
        lang=lang,
        tokenization=tokenization,
        min_num=min_num,
        max_num=max_num,
        batch_size=batch_size
    )

    # 处理数据
    if Fields.stats not in dataset.features:
        dataset = dataset.add_column(name=Fields.stats,
                                      column=[{}] * dataset.num_rows)
    dataset = dataset.map(op.compute_stats, batch_size=batch_size)
    dataset = dataset.filter(op.process, batch_size=batch_size)
    dataset = dataset.select_columns(column_names=['text'])

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
        description='单词数量过滤器 - 过滤单词数在指定范围内的样本'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--lang', type=str, default='en',
                        help='语言代码 (默认: en)')
    parser.add_argument('--tokenization', action='store_true',
                        help='是否使用分词模型')
    parser.add_argument('--min_num', type=int, default=10,
                        help='最小单词数量 (默认: 10)')
    parser.add_argument('--max_num', type=int, default=sys.maxsize,
                        help='最大单词数量 (默认: 不限制)')
    parser.add_argument('--batch_size', type=int, default=1,
                        help='批处理大小 (默认: 1)')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_words_num_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        lang=args.lang,
        tokenization=args.tokenization,
        min_num=args.min_num,
        max_num=args.max_num,
        batch_size=args.batch_size,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()