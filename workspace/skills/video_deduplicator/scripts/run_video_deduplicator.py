import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.deduplicator.video_deduplicator import VideoDeduplicator


class VideoDeduplicatorOp:
    """
    VideoDeduplicator算子封装类
    使用精确匹配在文档级别删除重复视频样本
    """

    def __init__(self,
                 consider_text: bool = False,
                 video_key: str = 'videos',
                 text_key: str = 'text'):
        self.consider_text = consider_text
        self.video_key = video_key
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行视频去重操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            samples = json.load(f)

        if not isinstance(samples, list):
            samples = [samples]

        dataset = Dataset.from_list(samples)

        op = VideoDeduplicator(consider_text=self.consider_text)

        dataset = dataset.map(op.compute_hash)
        dataset, _ = op.process(dataset)

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        deduplicated_count = len(res_list)
        removed_count = original_count - deduplicated_count

        print(f"[OK] Video deduplication completed!")
        print(f"   Consider text: {self.consider_text}")
        print(f"   Original documents: {original_count}")
        print(f"   Deduplicated documents: {deduplicated_count}")
        print(f"   Removed duplicates: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="VideoDeduplicator - 使用精确匹配在文档级别删除重复视频样本"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--consider_text', type=lambda x: x.lower() == 'true', default=False,
                        help='是否同时考虑文本哈希进行去重 (默认: False)')
    parser.add_argument('--video_key', type=str, default='videos',
                        help='视频字段的键名 (默认: videos)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    deduplicator = VideoDeduplicatorOp(
        consider_text=args.consider_text,
        video_key=args.video_key,
        text_key=args.text_key
    )

    deduplicator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
