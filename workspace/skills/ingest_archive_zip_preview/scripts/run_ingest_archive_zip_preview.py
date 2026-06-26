import argparse
import json
import os
import zipfile
from typing import Dict, Any


def ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def list_archives(root: str) -> list:
    archives = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith('.zip'):
                archives.append(os.path.join(dirpath, name))
    return archives


def preview_bytes(data: bytes, max_len: int) -> str:
    if max_len <= 0:
        return ''
    try:
        return data[:max_len].decode('utf-8')
    except UnicodeDecodeError:
        return data[:max_len].hex()


def process_archive(path: str, max_entries: int, preview_len: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'path': path,
        'type': 'zip',
        'entries': [],
        'total_entries': 0
    }
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            members = zf.infolist()
            record['total_entries'] = len(members)
            selected_members = members if max_entries <= 0 else members[:max_entries]
            for m in selected_members:
                entry = {
                    'name': m.filename,
                    'size': m.file_size,
                    'is_dir': m.is_dir()
                }
                if not m.is_dir() and preview_len > 0:
                    try:
                        data = zf.read(m)
                        entry['preview'] = preview_bytes(data, preview_len)
                    except Exception as exc:
                        entry['error'] = str(exc)
                record['entries'].append(entry)
    except Exception as exc:
        record['error'] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description='ZIP 压缩包内容预览')
    parser.add_argument('--input_dir', required=True, help='待扫描目录（递归）')
    parser.add_argument('--output', required=True, help='输出报告路径 (JSON)')
    parser.add_argument('--max_entries', type=int, default=0, help='每个压缩包最多列出的文件数，0 表示全部')
    parser.add_argument('--preview_bytes', type=int, default=200, help='文本文件预览字节数')
    args = parser.parse_args()

    archives = list_archives(args.input_dir)
    items = [process_archive(p, args.max_entries, args.preview_bytes) for p in archives]

    summary = {
        'total_archives': len(items),
        'errors': sum(1 for i in items if 'error' in i)
    }

    ensure_dir(args.output)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'items': items, 'summary': summary}, f, ensure_ascii=False, indent=2)

    print(f'[OK] ingest_archive_zip_preview completed')
    print(f"  Archives={summary['total_archives']} | errors={summary['errors']} | output={args.output}")


if __name__ == '__main__':
    main()
