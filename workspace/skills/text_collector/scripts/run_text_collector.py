import argparse
import json
import os
import csv
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')


class TextCollector:
    """
    文本类数据采集接入工具类
    适配纯文本类科研语料的读取与临时缓存，兼容不同编码和排版结构
    """

    SUPPORTED_EXTENSIONS = ['.txt', '.md', '.rst', '.log', '.text']
    COMMON_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'latin-1']

    def __init__(
        self,
        encoding: str = 'auto',
        recursive: bool = False,
        add_metadata: bool = True,
        output_format: str = 'jsonl'
    ):
        self.encoding = encoding
        self.recursive = recursive
        self.add_metadata = add_metadata
        self.output_format = output_format

    def _detect_encoding(self, file_path: str) -> str:
        """自动检测文件编码"""
        for enc in self.COMMON_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    f.read(1024)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return 'utf-8'

    def _read_text_file(self, file_path: str) -> str:
        """读取单个文本文件"""
        enc = self.encoding if self.encoding != 'auto' else self._detect_encoding(file_path)
        with open(file_path, 'r', encoding=enc, errors='replace') as f:
            return f.read()

    def _collect_files(self, input_path: str) -> list:
        """收集所有待处理文件"""
        files = []
        if os.path.isfile(input_path):
            if os.path.splitext(input_path)[1].lower() in self.SUPPORTED_EXTENSIONS:
                files.append(input_path)
        elif os.path.isdir(input_path):
            if self.recursive:
                for root, _, filenames in os.walk(input_path):
                    for fname in filenames:
                        if os.path.splitext(fname)[1].lower() in self.SUPPORTED_EXTENSIONS:
                            files.append(os.path.join(root, fname))
            else:
                for fname in os.listdir(input_path):
                    fp = os.path.join(input_path, fname)
                    if os.path.isfile(fp) and os.path.splitext(fname)[1].lower() in self.SUPPORTED_EXTENSIONS:
                        files.append(fp)
        else:
            raise FileNotFoundError(f"输入路径不存在: {input_path}")
        return sorted(files)

    def _write_output(self, records: list, output_path: str):
        """写入输出文件"""
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        fmt = self.output_format
        if fmt == 'auto':
            ext = os.path.splitext(output_path)[1].lower()
            fmt = {'.jsonl': 'jsonl', '.json': 'json', '.csv': 'csv'}.get(ext, 'jsonl')

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

    def perform(self, input_path: str, output_path: str) -> dict:
        """
        执行文本采集

        :param input_path: 输入文件或目录路径
        :param output_path: 输出文件路径
        :return: 采集统计信息
        """
        files = self._collect_files(input_path)
        total = len(files)
        if total == 0:
            raise ValueError(f"未找到支持的文本文件（{self.SUPPORTED_EXTENSIONS}）")

        records = []
        skipped = 0

        for fp in files:
            try:
                content = self._read_text_file(fp)
            except Exception as e:
                print(f"[WARN] 读取失败 {fp}: {e}")
                skipped += 1
                continue

            record = {'text': content}
            if self.add_metadata:
                stat = os.stat(fp)
                if os.path.isfile(input_path):
                    source_file = os.path.basename(fp)
                else:
                    source_file = os.path.relpath(fp, input_path).replace(os.sep, '/')
                record['_meta'] = {
                    'source_file': source_file,
                    'filename': os.path.basename(fp),
                    'file_size': stat.st_size,
                    'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'encoding': self.encoding if self.encoding != 'auto' else self._detect_encoding(fp)
                }
            records.append(record)

        self._write_output(records, output_path)

        collected = len(records)
        print(f"\n[OK] Text collection completed!")
        print(f"   Input path: {input_path}")
        print(f"   Total files found: {total}")
        print(f"   Collected: {collected}")
        print(f"   Skipped: {skipped}")
        print(f"   Output file: {output_path}")

        return {'total': total, 'collected': collected, 'skipped': skipped}


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
        description="TextCollector - 文本类数据采集接入工具"
    )
    parser.add_argument('--input', required=True, type=str,
                        help='输入文件或目录路径')
    parser.add_argument('--output', required=True, type=str,
                        help='输出文件路径')
    parser.add_argument('--encoding', type=str, default='auto',
                        help='文件编码，默认auto自动检测')
    parser.add_argument('--recursive', type=str_to_bool, default=False,
                        help='是否递归处理子目录，默认false')
    parser.add_argument('--add_metadata', type=str_to_bool, default=True,
                        help='是否添加文件元信息，默认true')
    parser.add_argument('--output_format', type=str, default='jsonl',
                        choices=['jsonl', 'json', 'csv', 'auto'],
                        help='输出格式，默认jsonl')

    args = parser.parse_args()

    collector = TextCollector(
        encoding=args.encoding,
        recursive=args.recursive,
        add_metadata=args.add_metadata,
        output_format=args.output_format
    )
    collector.perform(input_path=args.input, output_path=args.output)


if __name__ == '__main__':
    main()
