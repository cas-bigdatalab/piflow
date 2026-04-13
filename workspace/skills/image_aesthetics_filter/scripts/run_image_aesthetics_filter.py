import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.filter.image_aesthetics_filter import ImageAestheticsFilter
from data_juicer.utils.constant import Fields


class ImageAestheticsFilterOp:
    """
    ImageAestheticsFilter算子封装类
    过滤美学评分不在指定范围内的图像
    """

    def __init__(self,
                 hf_scorer_model: str = 'shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE',
                 min_score: float = 0.5,
                 max_score: float = 1.0,
                 any_or_all: str = 'any',
                 image_key: str = 'images'):
        self.hf_scorer_model = hf_scorer_model
        self.min_score = min_score
        self.max_score = max_score
        self.any_or_all = any_or_all
        self.image_key = image_key

    def perform(self, input_path: str, output_path: str):
        """
        执行图像美学过滤操作

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

        op = ImageAestheticsFilter(
            hf_scorer_model=self.hf_scorer_model,
            min_score=self.min_score,
            max_score=self.max_score,
            any_or_all=self.any_or_all
        )

        dataset = dataset.map(op.compute_stats_single)
        dataset = dataset.filter(op.process_single)
        dataset = dataset.remove_columns(Fields.stats)

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        filtered_count = len(res_list)
        removed_count = original_count - filtered_count

        print(f"[OK] Image aesthetics filtering completed!")
        print(f"   Scorer model: {self.hf_scorer_model}")
        print(f"   Min score: {self.min_score}")
        print(f"   Max score: {self.max_score}")
        print(f"   Strategy: {self.any_or_all}")
        print(f"   Original documents: {original_count}")
        print(f"   Filtered documents: {filtered_count}")
        print(f"   Removed documents: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ImageAestheticsFilter - 过滤美学评分不在指定范围内的图像"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--hf_scorer_model', type=str,
                        default='shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE',
                        help='美学评分模型 (默认: shunk031/aesthetics-predictor-v2-sac-logos-ava1-l14-linearMSE)')
    parser.add_argument('--min_score', type=float, default=0.5,
                        help='最小美学评分 (默认: 0.5)')
    parser.add_argument('--max_score', type=float, default=1.0,
                        help='最大美学评分 (默认: 1.0)')
    parser.add_argument('--any_or_all', type=str, default='any',
                        choices=['any', 'all'],
                        help='多图像过滤策略 (默认: any)')
    parser.add_argument('--image_key', type=str, default='images',
                        help='图像字段的键名 (默认: images)')

    args = parser.parse_args()

    filter_op = ImageAestheticsFilterOp(
        hf_scorer_model=args.hf_scorer_model,
        min_score=args.min_score,
        max_score=args.max_score,
        any_or_all=args.any_or_all,
        image_key=args.image_key
    )

    filter_op.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
