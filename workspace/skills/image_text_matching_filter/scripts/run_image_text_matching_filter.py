import argparse
import json
import os

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.image_text_matching_filter import ImageTextMatchingFilter
from data_juicer.utils.constant import Fields


def run_matching_filter(input_path: str, output_path: str,
                       hf_blip: str = 'Salesforce/blip-itm-base-coco',
                       min_score: float = 0.003,
                       max_score: float = 1.0,
                       horizontal_flip: bool = False,
                       vertical_flip: bool = False,
                       reduce_mode: str = 'avg',
                       any_or_all: str = 'any',
                       num_proc: int = 1):
    """
    运行图像文本匹配过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param hf_blip: BLIP模型名称
    :param min_score: 最小匹配分数
    :param max_score: 最大匹配分数
    :param horizontal_flip: 是否水平翻转图像
    :param vertical_flip: 是否垂直翻转图像
    :param reduce_mode: 多图聚合模式
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
    op = ImageTextMatchingFilter(
        hf_blip=hf_blip,
        min_score=min_score,
        max_score=max_score,
        horizontal_flip=horizontal_flip,
        vertical_flip=vertical_flip,
        reduce_mode=reduce_mode,
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
    dataset = dataset.select_columns(column_names=['text', 'images'])

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
        description='图像文本匹配过滤器 - 过滤图像文本匹配分数在指定范围内的样本'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--hf_blip', type=str,
                        default='Salesforce/blip-itm-base-coco',
                        help='BLIP模型 (默认: Salesforce/blip-itm-base-coco)')
    parser.add_argument('--min_score', type=float, default=0.003,
                        help='最小匹配分数 (默认: 0.003)')
    parser.add_argument('--max_score', type=float, default=1.0,
                        help='最大匹配分数 (默认: 1.0)')
    parser.add_argument('--horizontal_flip', action='store_true',
                        help='是否水平翻转图像')
    parser.add_argument('--vertical_flip', action='store_true',
                        help='是否垂直翻转图像')
    parser.add_argument('--reduce_mode', type=str, default='avg',
                        choices=['avg', 'max', 'min'],
                        help='多图聚合模式: avg/max/min (默认: avg)')
    parser.add_argument('--any_or_all', type=str, default='any',
                        choices=['any', 'all'],
                        help='过滤策略: any=任意一个符合保留, all=所有都符合保留 (默认: any)')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')

    args = parser.parse_args()

    run_matching_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        hf_blip=args.hf_blip,
        min_score=args.min_score,
        max_score=args.max_score,
        horizontal_flip=args.horizontal_flip,
        vertical_flip=args.vertical_flip,
        reduce_mode=args.reduce_mode,
        any_or_all=args.any_or_all,
        num_proc=args.num_proc
    )


if __name__ == '__main__':
    main()