import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.average_line_length_filter import AverageLineLengthFilter
from data_juicer.utils.constant import Fields


class AverageLineLengthFilterOp:
    """
    AverageLineLengthFilter算子封装类
    过滤平均行长度不在指定范围内的样本
    """

    def __init__(self,
                 min_len: float = 10,
                 max_len: float = None,
                 text_key: str = 'text'):
        self.min_len = min_len
        self.max_len = max_len if max_len is not None else float('inf')
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行平均行长度过滤操作

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

        if Fields.stats not in dataset.features:
            dataset = dataset.add_column(
                name=Fields.stats,
                column=[{}] * dataset.num_rows
            )

        op = AverageLineLengthFilter(
            min_len=self.min_len,
            max_len=self.max_len
        )

        dataset = dataset.map(
            op.compute_stats_batched,
            batch_size=op.batch_size
        )
        dataset = dataset.filter(op.process_batched, batch_size=op.batch_size)
        dataset = dataset.select_columns(column_names=[self.text_key])

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        filtered_count = len(res_list)
        removed_count = original_count - filtered_count

        print(f"[OK] Average line length filtering completed!")
        print(f"   Min length: {self.min_len}")
        print(f"   Max length: {self.max_len if self.max_len != float('inf') else 'unlimited'}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="AverageLineLengthFilter - 过滤平均行长度不在指定范围内的样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--min_len', type=float, default=10,
                        help='最小平均行长度 (默认: 10)')
    parser.add_argument('--max_len', type=float, default=None,
                        help='最大平均行长度 (默认: 无限制)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    filter_op = AverageLineLengthFilterOp(
        min_len=args.min_len,
        max_len=args.max_len,
        text_key=args.text_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
