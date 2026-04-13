import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.alphanumeric_filter import AlphanumericFilter


class AlphanumericFilterOp:
    """
    AlphanumericFilter算子封装类
    过滤字母/数字比例不在指定范围内的样本
    """

    def __init__(self,
                 min_ratio: float = 0.25,
                 max_ratio: float = 1.0,
                 tokenization: bool = False,
                 text_key: str = 'text'):
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
        self.tokenization = tokenization
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行字母数字比例过滤操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)

        if isinstance(input_data, dict) and 'data' in input_data:
            samples = input_data['data']
        elif isinstance(input_data, list):
            samples = input_data
        else:
            samples = [input_data]

        dataset = Dataset.from_list(samples)

        op = AlphanumericFilter(
            min_ratio=self.min_ratio,
            max_ratio=self.max_ratio,
            tokenization=self.tokenization
        )

        dataset = dataset.map(op.compute_stats_batched)
        dataset = dataset.filter(op.process_batched)

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        filtered_count = len(res_list)
        removed_count = original_count - filtered_count

        print(f"[OK] Alphanumeric filtering completed!")
        print(f"   Min ratio: {self.min_ratio}")
        print(f"   Max ratio: {self.max_ratio}")
        print(f"   Tokenization: {self.tokenization}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AlphanumericFilter - 过滤字母/数字比例不在指定范围内的样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--min_ratio', type=float, default=0.25,
                        help='最小字母数字比例 (默认: 0.25)')
    parser.add_argument('--max_ratio', type=float, default=1.0,
                        help='最大字母数字比例 (默认: 1.0)')
    parser.add_argument('--tokenization', type=lambda x: x.lower() == 'true', default=False,
                        help='是否使用tokenization计算比例 (默认: False)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    if args.max_ratio > 1.0:
        import sys
        args.max_ratio = sys.maxsize

    filter_op = AlphanumericFilterOp(
        min_ratio=args.min_ratio,
        max_ratio=args.max_ratio,
        tokenization=args.tokenization,
        text_key=args.text_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
