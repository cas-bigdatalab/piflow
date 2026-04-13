import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.image_aspect_ratio_filter import ImageAspectRatioFilter
from data_juicer.utils.constant import Fields


class ImageAspectRatioFilterOp:
    """
    ImageAspectRatioFilter算子封装类
    过滤长宽比不在指定范围内的图像
    """

    def __init__(self,
                 min_ratio: float = 0.333,
                 max_ratio: float = 3.0,
                 any_or_all: str = 'any',
                 image_key: str = 'images'):
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio
        self.any_or_all = any_or_all
        self.image_key = image_key

    def perform(self, input_path: str, output_path: str):
        """
        执行图像长宽比过滤操作

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

        op = ImageAspectRatioFilter(
            min_ratio=self.min_ratio,
            max_ratio=self.max_ratio,
            any_or_all=self.any_or_all
        )

        dataset = dataset.map(op.compute_stats_batched, batch_size=op.batch_size)
        dataset = dataset.filter(op.process_batched, batch_size=op.batch_size)
        dataset = dataset.select_columns(column_names=[self.image_key])

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        filtered_count = len(res_list)
        removed_count = original_count - filtered_count

        print(f"[OK] Image aspect ratio filtering completed!")
        print(f"   Min ratio: {self.min_ratio}")
        print(f"   Max ratio: {self.max_ratio}")
        print(f"   Strategy: {self.any_or_all}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ImageAspectRatioFilter - 过滤长宽比不在指定范围内的图像"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--min_ratio', type=float, default=0.333,
                        help='最小长宽比 (默认: 0.333)')
    parser.add_argument('--max_ratio', type=float, default=3.0,
                        help='最大长宽比 (默认: 3.0)')
    parser.add_argument('--any_or_all', type=str, default='any',
                        choices=['any', 'all'],
                        help='多图像过滤策略 (默认: any)')
    parser.add_argument('--image_key', type=str, default='images',
                        help='图像字段的键名 (默认: images)')

    args = parser.parse_args()

    filter_op = ImageAspectRatioFilterOp(
        min_ratio=args.min_ratio,
        max_ratio=args.max_ratio,
        any_or_all=args.any_or_all,
        image_key=args.image_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
