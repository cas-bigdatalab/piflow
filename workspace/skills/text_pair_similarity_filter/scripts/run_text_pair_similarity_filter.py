import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.text_pair_similarity_filter import TextPairSimilarityFilter
from data_juicer.utils.constant import Fields


def run_text_pair_similarity_filter(input_path: str, output_path: str,
                              text_key_second: str,
                              hf_clip: str = 'openai/clip-vit-base-patch32',
                              min_score: float = 0.1,
                              max_score: float = 1.0,
                              any_or_all: str = 'any',
                              num_proc: int = 1):
    """
    运行文本对相似度过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param text_key_second: 第二个文本字段名
    :param hf_clip: CLIP模型名称
    :param min_score: 最小相似度分数
    :param max_score: 最大相似度分数
    :param any_or_all: 过滤策略
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
    op = TextPairSimilarityFilter(
        hf_clip=hf_clip,
        min_score=min_score,
        max_score=max_score,
        text_key_second=text_key_second,
        any_or_all=any_or_all
    )

    # 处理数据
    if Fields.stats not in dataset.features:
        dataset = dataset.add_column(name=Fields.stats,
                                      column=[{}] * dataset.num_rows)
    dataset = dataset.map(op.compute_stats,
                          num_proc=num_proc,
                          with_rank=True)
    dataset = dataset.filter(op.process, num_proc=num_proc)
    dataset = dataset.select_columns(column_names=['text', text_key_second])

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
        description='文本对相似度过滤器 - 过滤文本对相似度在指定范围内的样本'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--text_key_second', type=str, required=True,
                        help='第二个文本字段名')
    parser.add_argument('--hf_clip', type=str,
                        default='openai/clip-vit-base-patch32',
                        help='CLIP模型 (默认: openai/clip-vit-base-patch32)')
    parser.add_argument('--min_score', type=float, default=0.1,
                        help='最小相似度分数 (默认: 0.1)')
    parser.add_argument('--max_score', type=float, default=1.0,
                        help='最大相似度分数 (默认: 1.0)')
    parser.add_argument('--any_or_all', type=str, default='any',
                        choices=['any', 'all'],
                        help='过滤策略: any=任意一个符合保留, all=所有都符合保留 (默认: any)')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_text_pair_similarity_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        text_key_second=args.text_key_second,
        hf_clip=args.hf_clip,
        min_score=args.min_score,
        max_score=args.max_score,
        any_or_all=args.any_or_all,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()