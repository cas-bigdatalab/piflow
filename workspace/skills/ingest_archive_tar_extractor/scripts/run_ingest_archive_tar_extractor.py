import argparse
import json
import os
import tarfile
from typing import Dict, Any

TAR_EXTENSIONS = {'.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2', '.txz'}


def ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def list_archives(root: str) -> list:
    archives = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            lower = name.lower()
            if any(lower.endswith(ext) for ext in TAR_EXTENSIONS):
                archives.append(os.path.join(dirpath, name))
    return archives


def extract_archive(path: str, output_dir: str, max_entries: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'path': path,
        'type': 'tar',
        'extracted': [],
        'error': None
    }
    try:
        mode = 'r'
        lower = path.lower()
        if lower.endswith('.gz') or lower.endswith('.tgz'):
            mode = 'r:gz'
        elif lower.endswith('.bz2') or lower.endswith('.tbz2'):
            mode = 'r:bz2'
        elif lower.endswith('.xz') or lower.endswith('.txz'):
            mode = 'r:xz'
        with tarfile.open(path, mode) as tf:
            members = tf.getmembers()
            if max_entries > 0:
                members = members[:max_entries]
            for m in members:
                try:
                    tf.extract(m, path=output_dir, filter='data')
                    record['extracted'].append(m.name)
                except Exception as exc:
                    record.setdefault('failed', []).append({'member': m.name, 'error': str(exc)})
    except Exception as exc:
        record['error'] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description='TAR 压缩包解压')
    parser.add_argument('--input_dir', required=True, help='待解压目录（递归）')
    parser.add_argument('--output_dir', required=True, help='输出根目录')
    parser.add_argument('--report', required=True, help='报告输出路径 (JSON)')
    parser.add_argument('--max_entries', type=int, default=0, help='单包最大解压文件数，0 不限')
    args = parser.parse_args()

    ensure_dir(args.output_dir)

    archives = list_archives(args.input_dir)
    items = [extract_archive(p, args.output_dir, args.max_entries) for p in archives]

    summary = {
        'total_archives': len(items),
        'errors': sum(1 for i in items if i.get('error'))
    }

    ensure_dir(args.report)
    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump({'items': items, 'summary': summary}, f, ensure_ascii=False, indent=2)

    print(f'[OK] ingest_archive_tar_extractor completed')
    print(f"  Archives={summary['total_archives']} | errors={summary['errors']} | report={args.report}")


if __name__ == '__main__':
    main()
