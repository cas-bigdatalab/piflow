import argparse
import json
import os
import sys

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.token_num_filter import TokenNumFilter
from data_juicer.utils.constant import Fields


def run_token_num_filter(input_path: str, output_path: str,
                    hf_tokenizer: str = 'EleutherAI/pythia-6.9b-deduped',
                    min_num: int = 10,
                    max_num: int = sys.maxsize,
                    num_proc: int = 1,
                         text_key: str = "text"):
    """
    运行Token数量过滤算子

    :param input_path: 输入文件路径 (JSON/JSONL)
    :param output_path: 输出文件路径 (JSONL)
    :param hf_tokenizer: HuggingFace tokenizer 模型
    :param min_num: 最小 token 数量
    :param max_num: 最大 token 数量
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
    op = TokenNumFilter(
        hf_tokenizer=hf_tokenizer,
        min_num=min_num,
        max_num=max_num,
        text_key=text_key,
    )

    # 处理数据
    if Fields.stats not in dataset.features:
        dataset = dataset.add_column(name=Fields.stats,
                                      column=[{}] * dataset.num_rows)
    dataset = dataset.map(op.compute_stats, num_proc=num_proc)
    dataset = dataset.filter(op.process, num_proc=num_proc)

    # 保存结果
    res_list = dataset.to_list()
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in res_list:
            item.pop(Fields.stats, None)
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: 输入 {len(ds_list)} 条 -> 输出 {len(res_list)} 条")
    print(f"结果已保存至: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Token数量过滤器 - 过滤token数在指定范围内的文本'
    )
    parser.add_argument('--input_path', type=str, required=True,
                        help='输入数据文件路径 (JSON/JSONL格式)')
    parser.add_argument('--output_path', type=str, required=True,
                        help='输出数据文件路径 (JSONL格式)')
    parser.add_argument('--hf_tokenizer', type=str,
                        default='EleutherAI/pythia-6.9b-deduped',
                        help='HuggingFace tokenizer模型 (默认: EleutherAI/pythia-6.9b-deduped)')
    parser.add_argument('--min_num', type=int, default=10,
                        help='最小token数量 (默认: 10)')
    parser.add_argument('--max_num', type=int, default=sys.maxsize,
                        help='最大token数量 (默认: 不限制)')
    parser.add_argument('--num_proc', type=int, default=1,
                        help='并行进程数 (默认: 1)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='要操作的文本字段名 (默认: text)')

    args = parser.parse_args()

    run_token_num_filter(
        input_path=args.input_path,
        output_path=args.output_path,
        hf_tokenizer=args.hf_tokenizer,
        min_num=args.min_num,
        max_num=args.max_num,
        num_proc=args.num_proc,
        text_key=args.text_key,
    )


if __name__ == '__main__':
    main()