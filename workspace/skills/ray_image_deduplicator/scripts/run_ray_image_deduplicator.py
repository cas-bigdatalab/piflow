import argparse
import json

from data_juicer.core.data import NestedDataset as Dataset
from data_juicer.ops.deduplicator.ray_image_deduplicator import RayImageDeduplicator


class RayImageDeduplicatorOp:
    """
    RayImageDeduplicator算子封装类
    使用Ray分布式框架进行图像去重
    """

    def __init__(self,
                 method: str = 'phash',
                 backend: str = 'ray_actor',
                 redis_address: str = 'redis://localhost:6379',
                 image_key: str = 'images',
                 text_key: str = 'text'):
        self.method = method
        self.backend = backend
        self.redis_address = redis_address
        self.image_key = image_key
        self.text_key = text_key

    def perform(self, input_path: str, output_path: str):
        """
        执行图像去重操作

        :param input_path: 输入JSON文件路径
        :param output_path: 输出JSON文件路径
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            samples = json.load(f)

        if not isinstance(samples, list):
            samples = [samples]

        dataset = Dataset.from_list(samples)

        op = RayImageDeduplicator(
            method=self.method,
            backend=self.backend,
            redis_address=self.redis_address
        )

        dataset = dataset.map(op.calculate_hash)
        dataset, _ = op.process(dataset)

        res_list = dataset.to_list()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res_list, f, ensure_ascii=False, indent=2)

        original_count = len(samples)
        deduplicated_count = len(res_list)
        removed_count = original_count - deduplicated_count

        print(f"[OK] Ray image deduplication completed!")
        print(f"   Method: {self.method}")
        print(f"   Backend: {self.backend}")
        print(f"   Original documents: {original_count}")
        print(f"   Deduplicated documents: {deduplicated_count}")
        print(f"   Removed duplicates: {removed_count}")
        print(f"   Input file: {input_path}")
        print(f"   Output file: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="RayImageDeduplicator - 使用Ray分布式框架进行图像去重"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入JSON文件路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出JSON文件路径')
    parser.add_argument('--method', type=str, default='phash',
                        choices=['phash', 'dhash', 'whash', 'ahash'],
                        help='图像哈希方法 (默认: phash)')
    parser.add_argument('--backend', type=str, default='ray_actor',
                        choices=['ray_actor', 'redis'],
                        help='分布式后端 (默认: ray_actor)')
    parser.add_argument('--redis_address', type=str, default='redis://localhost:6379',
                        help='Redis地址 (默认: redis://localhost:6379)')
    parser.add_argument('--image_key', type=str, default='images',
                        help='图像字段的键名 (默认: images)')
    parser.add_argument('--text_key', type=str, default='text',
                        help='文本字段的键名 (默认: text)')

    args = parser.parse_args()

    deduplicator = RayImageDeduplicatorOp(
        method=args.method,
        backend=args.backend,
        redis_address=args.redis_address,
        image_key=args.image_key,
        text_key=args.text_key
    )

    deduplicator.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
