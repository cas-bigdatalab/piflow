import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.character_repetition_filter import CharacterRepetitionFilter
from data_juicer.utils.constant import Fields


class CharacterRepetitionFilterOp:
    """
    CharacterRepetitionFilter算子封装类
    过滤字符级n-gram重复比例不在指定范围内的样本
    """

    def __init__(self,
                 rep_len: int = 10,
                 min_ratio: float = 0.0,
                 max_ratio: float = 0.5,
                 text_key: str = 'text'):
        self.rep_len = rep_len
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行字符重复比例过滤操作

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

        op = CharacterRepetitionFilter(
            rep_len=self.rep_len,
            min_ratio=self.min_ratio,
            max_ratio=self.max_ratio
        )

        dataset = dataset.map(op.compute_stats_batched, batch_size=op.batch_size)
        dataset = dataset.filter(op.process_batched, batch_size=op.batch_size)
        dataset = dataset.select_columns(column_names=[self.text_key])

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        filtered_count = len(res_list)
        removed_count = original_count - filtered_count

        print(f"[OK] Character repetition filtering completed!")
        print(f"   Rep length: {self.rep_len}")
        print(f"   Min ratio: {self.min_ratio}")
        print(f"   Max ratio: {self.max_ratio}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="CharacterRepetitionFilter - 过滤字符级n-gram重复比例不在指定范围内的样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--rep_len', type=int, default=10,
                        help='字符级n-gram重复长度 (默认: 10)')
    parser.add_argument('--min_ratio', type=float, default=0.0,
                        help='最小重复比例 (默认: 0.0)')
    parser.add_argument('--max_ratio', type=float, default=0.5,
                        help='最大重复比例 (默认: 0.5)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    filter_op = CharacterRepetitionFilterOp(
        rep_len=args.rep_len,
        min_ratio=args.min_ratio,
        max_ratio=args.max_ratio,
        text_key=args.text_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
