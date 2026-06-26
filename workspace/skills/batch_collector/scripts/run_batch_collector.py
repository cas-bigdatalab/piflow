import argparse
import json
import os
import csv
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


class BatchCollector:
    """
    批量任务采集工具类
    面向规模化科研语料生产场景，提供批量数据集中采集能力
    支持任务队列排布，按照预设顺序自动执行采集作业
    """

    SUPPORTED_EXTENSIONS = [
        '.txt', '.md', '.rst', '.log',
        '.csv', '.tsv',
        '.pdf', '.docx', '.doc',
        '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp',
        '.json', '.jsonl'
    ]

    def __init__(
        self,
        output_format: str = 'jsonl',
        recursive: bool = False,
        add_metadata: bool = True,
        file_types: list = None,
        batch_size: int = 0,
        encoding: str = 'auto'
    ):
        self.output_format = output_format
        self.recursive = recursive
        self.add_metadata = add_metadata
        self.file_types = [f'.{t.lstrip(".")}' for t in file_types] if file_types else self.SUPPORTED_EXTENSIONS
        self.batch_size = batch_size
        self.encoding = encoding

    def _collect_files(self, input_paths: list) -> list:
        """从多个输入路径收集文件"""
        files = []
        for path in input_paths:
            if os.path.isfile(path):
                if os.path.splitext(path)[1].lower() in self.file_types:
                    files.append(path)
            elif os.path.isdir(path):
                walk = os.walk(path) if self.recursive else [(path, [], os.listdir(path))]
                for root, _, filenames in walk:
                    for fname in filenames:
                        fp = os.path.join(root, fname)
                        if os.path.isfile(fp) and os.path.splitext(fp)[1].lower() in self.file_types:
                            files.append(fp)
            else:
                print(f"[WARN] 路径不存在，已跳过: {path}")
        return sorted(set(files))

    def _read_task_list(self, task_list_path: str) -> list:
        """从任务列表文件读取输入路径"""
        ext = os.path.splitext(task_list_path)[1].lower()
        paths = []
        if ext == '.json':
            with open(task_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                paths = [str(p) for p in data]
            elif isinstance(data, dict):
                paths = data.get('paths', data.get('inputs', []))
        elif ext in ['.txt', '.lst']:
            with open(task_list_path, 'r', encoding='utf-8') as f:
                paths = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        else:
            raise ValueError(f"不支持的任务列表格式: {ext}，支持 json/txt/lst")
        return paths

    def _get_file_info(self, fp: str, input_paths: list = None) -> dict:
        """获取文件基本信息"""
        stat = os.stat(fp)
        # derive relative path from the first input path, or from file's parent
        if input_paths:
            for base in input_paths:
                try:
                    rel = os.path.relpath(fp, base)
                    if not rel.startswith('..'):
                        source_file = rel.replace(os.sep, '/')
                        break
                except ValueError:
                    continue
            else:
                source_file = os.path.basename(fp)
        else:
            source_file = os.path.basename(fp)
        return {
            'file_path': source_file,
            'filename': os.path.basename(fp),
            'extension': os.path.splitext(fp)[1].lower(),
            'file_size': stat.st_size,
            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _write_output(self, records: list, output_path: str):
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        fmt = self.output_format
        if fmt == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            fmt = {'.json': 'json', '.csv': 'csv'}.get(ext, 'jsonl')

        if fmt == 'jsonl':
            with open(output_path, 'w', encoding='utf-8') as f:
                for rec in records:
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        elif fmt == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        elif fmt == 'csv':
            if records:
                with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=records[0].keys())
                    writer.writeheader()
                    writer.writerows(records)

    def perform(self, input_paths: list, output_path: str, task_list: str = None) -> dict:
        """
        执行批量采集

        :param input_paths: 输入路径列表
        :param output_path: 输出文件路径
        :param task_list: 任务列表文件路径（可选，优先于input_paths）
        """
        if task_list:
            input_paths = self._read_task_list(task_list)
            print(f"[INFO] 从任务列表加载 {len(input_paths)} 个路径")

        all_files = self._collect_files(input_paths)
        total = len(all_files)

        if total == 0:
            raise ValueError("未找到任何符合条件的文件")

        records = []
        type_counts = {}

        for i, fp in enumerate(all_files):
            ext = os.path.splitext(fp)[1].lower().lstrip('.')
            type_counts[ext] = type_counts.get(ext, 0) + 1
            record = self._get_file_info(fp, input_paths=input_paths)
            record['task_index'] = i + 1
            record['total_tasks'] = total
            records.append(record)

            if self.batch_size > 0 and (i + 1) % self.batch_size == 0:
                print(f"[INFO] 已处理 {i + 1}/{total} 个文件")

        self._write_output(records, output_path)

        print(f"\n[OK] Batch collection completed!")
        print(f"   Input paths: {len(input_paths)}")
        print(f"   Total files collected: {total}")
        print(f"   File type distribution:")
        for ext, cnt in sorted(type_counts.items()):
            print(f"     - .{ext}: {cnt}")
        print(f"   Output: {output_path}")

        return {'input_paths': len(input_paths), 'total_files': total, 'type_counts': type_counts}


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes'):
        return True
    elif value.lower() in ('false', '0', 'no'):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


def main():
    parser = argparse.ArgumentParser(
        description="BatchCollector - 批量任务采集工具"
    )
    parser.add_argument('--input', nargs='+', type=str, default=[],
                        help='输入文件或目录路径，支持多个')
    parser.add_argument('--task_list', type=str, default=None,
                        help='任务列表文件路径（json/txt），与--input二选一')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--recursive', type=str_to_bool, default=False,
                        help='是否递归处理子目录，默认false')
    parser.add_argument('--file_types', nargs='+', type=str, default=None,
                        help='指定采集的文件类型，如 txt csv pdf，默认全部支持类型')
    parser.add_argument('--batch_size', type=int, default=0,
                        help='批量进度报告间隔，0表示不报告')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'csv', 'auto'],
                        help='输出格式，默认jsonl')

    args = parser.parse_args()

    if not args.input and not args.task_list:
        parser.error("必须提供 --input 或 --task_list 之一")

    collector = BatchCollector(
        output_format=args.output_format,
        recursive=args.recursive,
        file_types=args.file_types,
        batch_size=args.batch_size
    )
    collector.perform(
        input_paths=args.input,
        output_path=args.output,
        task_list=args.task_list
    )


if __name__ == '__main__':
    main()
