import argparse
import json
import os
import random
import math
import warnings

warnings.filterwarnings('ignore')


class BatchDataSplitter:
    """
    批量数据均匀分割工具类
    将大容量数据集均匀划分为多组子数据集
    """

    def __init__(
        self,
        num_splits: int = 0,
        chunk_size: int = 1000,
        output_prefix: str = 'split',
        shuffle: bool = False,
        random_seed: int = 42
    ):
        self.num_splits = num_splits
        self.chunk_size = chunk_size
        self.output_prefix = output_prefix
        self.shuffle = shuffle
        self.random_seed = random_seed

        if shuffle:
            random.seed(random_seed)

        self.stats = {
            'total': 0,
            'num_splits': 0,
            'samples_per_split': [],
            'output_files': []
        }

    def _read_input(self, input_path: str) -> tuple:
        """读取输入文件"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"文件不存在: {input_path}")

        file_ext = os.path.splitext(input_path)[1].lower()
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

        data = []

        if file_ext == '.jsonl':
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                data.append(json.loads(line))
                    break
                except UnicodeDecodeError:
                    continue
            return data, 'jsonl'

        elif file_ext == '.json':
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data, 'json'
                        else:
                            return [data], 'json'
                except UnicodeDecodeError:
                    continue

        elif file_ext == '.csv':
            import csv
            for encoding in encodings:
                try:
                    with open(input_path, 'r', encoding=encoding, newline='') as f:
                        reader = csv.DictReader(f)
                        data = list(reader)
                    return data, 'csv'
                except UnicodeDecodeError:
                    continue

        raise ValueError(f"不支持的文件格式: {file_ext}")

    def _write_split(self, data: list, output_path: str, file_format: str):
        """写入分割文件"""
        if file_format == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        elif file_format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        elif file_format == 'csv':
            import csv
            if data:
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

    def perform(self, input_path: str, output_manifest: str) -> dict:
        """
        执行数据分割

        :param input_path: 输入文件路径
        :param output_manifest: 输出清单文件路径（JSON），实际分割文件写入同名 _splits/ 子目录
        :return: 处理结果统计
        """
        # 重置统计
        self.stats = {
            'total': 0,
            'num_splits': 0,
            'samples_per_split': [],
            'output_files': []
        }

        # 清单文件路径 → 分割目录 = <manifest>_splits/
        manifest_dir = os.path.dirname(os.path.abspath(output_manifest))
        manifest_basename = os.path.splitext(os.path.basename(output_manifest))[0]
        split_dir = os.path.join(manifest_dir, f"{manifest_basename}_splits")

        if not os.path.exists(split_dir):
            os.makedirs(split_dir)

        # 读取输入
        data, file_format = self._read_input(input_path)
        self.stats['total'] = len(data)

        # 打乱顺序
        if self.shuffle:
            random.shuffle(data)

        # 计算分割数量
        total = len(data)
        if total == 0:
            num_splits = 0
            chunk_size = 0
        elif self.num_splits > 0:
            num_splits = min(self.num_splits, total)
            chunk_size = math.ceil(total / num_splits)
        else:
            chunk_size = self.chunk_size
            num_splits = math.ceil(total / chunk_size)

        self.stats['num_splits'] = num_splits

        # 分割并写入
        ext = os.path.splitext(input_path)[1]
        for i in range(num_splits):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total)
            split_data = data[start_idx:end_idx]

            output_filename = f"{self.output_prefix}_{str(i + 1).zfill(3)}{ext}"
            output_path = os.path.join(split_dir, output_filename)

            self._write_split(split_data, output_path, file_format)

            self.stats['samples_per_split'].append(len(split_data))
            self.stats['output_files'].append(output_path)

        # 写清单 JSON（下游节点可消费的单文件输出）
        manifest = {
            'input_file': input_path,
            'input_format': file_format,
            'splits_dir': split_dir,
            'total_count': self.stats['total'],
            'actual_num_splits': self.stats['num_splits'],
            'samples_per_split': self.stats['samples_per_split'],
            'output_files': self.stats['output_files']
        }
        with open(output_manifest, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # 打印结果
        self._print_results(input_path, output_manifest, split_dir)

        return self.stats

    def _print_results(self, input_path, output_manifest, split_dir):
        """打印处理结果"""
        print(f"\n[OK] Batch data splitting completed!")
        print(f"   Input file: {input_path}")
        print(f"   Total samples: {self.stats['total']}")
        print(f"   Number of splits: {self.stats['num_splits']}")
        print(f"   Samples per split: {self.stats['samples_per_split']}")
        print(f"   Manifest file: {output_manifest}")
        print(f"   Splits directory: {split_dir}")
        print(f"   Output files:")
        for i, (path, count) in enumerate(zip(self.stats['output_files'], self.stats['samples_per_split'])):
            if i < 5:  # 只显示前5个
                print(f"     - {os.path.basename(path)} ({count} samples)")
            elif i == 5:
                print(f"     ... and {len(self.stats['output_files']) - 5} more files")
                break


def str_to_bool(value):
    """将字符串转换为布尔值"""
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'no'):
        return False
    else:
        raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="BatchDataSplitter - 批量数据均匀分割工具"
    )

    parser.add_argument('--input', required=True, type=str,
                        help='输入文件路径')
    parser.add_argument('--output_dir', required=True, type=str,
                        help='输出清单文件路径（JSON），实际分割文件写入同名 _splits/ 子目录')
    parser.add_argument('--num_splits', type=int, default=0,
                        help='分割份数，默认0')
    parser.add_argument('--chunk_size', type=int, default=1000,
                        help='每份样本数量，默认1000')
    parser.add_argument('--output_prefix', type=str, default='split',
                        help='输出文件名前缀，默认split')
    parser.add_argument('--shuffle', type=str_to_bool, default=False,
                        help='是否打乱顺序，默认false')
    parser.add_argument('--random_seed', type=int, default=42,
                        help='随机种子，默认42')

    args = parser.parse_args()

    # 诊断日志：完整打印引擎传入的实参，方便排查参数丢失
    print(f"[DIAG] received args: input={args.input}, output_dir={args.output_dir}, "
          f"num_splits={args.num_splits}, chunk_size={args.chunk_size}, "
          f"output_prefix={args.output_prefix}, shuffle={args.shuffle}, "
          f"random_seed={args.random_seed}")

    splitter = BatchDataSplitter(
        num_splits=args.num_splits,
        chunk_size=args.chunk_size,
        output_prefix=args.output_prefix,
        shuffle=args.shuffle,
        random_seed=args.random_seed
    )

    splitter.perform(input_path=args.input, output_manifest=args.output_dir)


if __name__ == '__main__':
    main()
