import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.stopwords_filter import StopWordsFilter
from data_juicer.utils.constant import Fields


def run_stopwords_filter(input_path: str, output_path: str,
                        lang: str = 'en',
                        tokenization: bool = False,
                        min_ratio: float = 0.3,
                        use_words_aug: bool = False,
                        num_proc: int = 1):
    """
    运行停用词过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param lang: 语言代码
    :param tokenization: 是否使用分词模型
    :param min_ratio: 最小停用词比例
    :param use_words_aug: 是否使用词语增强
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
    op = StopWordsFilter(
        lang=lang,
        tokenization=tokenization,
        min_ratio=min_ratio,
        use_words_aug=use_words_aug
    )

    # 处理数据
    if Fields.stats not in dataset.features:
        dataset = dataset.add_column(name=Fields.stats,
                                      column=[{}] * dataset.num_rows)
    dataset = dataset.map(op.compute_stats, num_proc=num_proc)
    dataset = dataset.filter(op.process, num_proc=num_proc)
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
        description='停用词过滤器 - 过滤停用词比例大于指定值的样本'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--lang', type=str, default='en',
                        help='语言代码 (默认: en)')
    parser.add_argument('--tokenization', action='store_true',
                        help='是否使用分词模型')
    parser.add_argument('--min_ratio', type=float, default=0.3,
                        help='最小停用词比例 (默认: 0.3)')
    parser.add_argument('--use_words_aug', action='store_true',
                        help='是否使用词语增强')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_stopwords_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        lang=args.lang,
        tokenization=args.tokenization,
        min_ratio=args.min_ratio,
        use_words_aug=args.use_words_aug,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()