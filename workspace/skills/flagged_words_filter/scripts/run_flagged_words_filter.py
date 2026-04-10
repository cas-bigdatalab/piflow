import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.flagged_words_filter import FlaggedWordFilter
from data_juicer.utils.constant import Fields


class FlaggedWordsFilterOp:
    """
    FlaggedWordFilter算子封装类
    过滤包含敏感词/标记词的文本
    """

    def __init__(self,
                 lang: str = 'en',
                 tokenization: bool = False,
                 max_ratio: float = 0.045,
                 use_words_aug: bool = False,
                 text_key: str = 'text'):
        self.lang = lang
        self.tokenization = tokenization
        self.max_ratio = max_ratio
        self.use_words_aug = use_words_aug
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行敏感词过滤操作

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

        op = FlaggedWordFilter(
            lang=self.lang,
            tokenization=self.tokenization,
            max_ratio=self.max_ratio,
            use_words_aug=self.use_words_aug
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

        print(f"[OK] Flagged words filtering completed!")
        print(f"   Language: {self.lang}")
        print(f"   Max ratio: {self.max_ratio}")
        print(f"   Tokenization: {self.tokenization}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="FlaggedWordFilter - 过滤包含敏感词/标记词的文本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--lang', type=str, default='en',
                        help='语言 (en/zh/all, 默认: en)')
    parser.add_argument('--tokenization', type=lambda x: x.lower() == 'true', default=False,
                        help='是否使用模型分词 (默认: False)')
    parser.add_argument('--max_ratio', type=float, default=0.045,
                        help='最大敏感词比例 (默认: 0.045)')
    parser.add_argument('--use_words_aug', type=lambda x: x.lower() == 'true', default=False,
                        help='是否使用词语增强 (默认: False)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    filter_op = FlaggedWordsFilterOp(
        lang=args.lang,
        tokenization=args.tokenization,
        max_ratio=args.max_ratio,
        use_words_aug=args.use_words_aug,
        text_key=args.text_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
