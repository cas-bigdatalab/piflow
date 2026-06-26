import argparse
import json
import os
import subprocess
from typing import Dict, Any

try:
    import rarfile
except ImportError:
    rarfile = None

RAR_EXE_CANDIDATES = [
    r'D:/Program Files/WinRAR/Rar.exe',
    r'D:/Program Files (x86)/WinRAR/Rar.exe',
]


def ensure_dir(path: str):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def list_archives(root: str) -> list:
    archives = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if name.lower().endswith('.rar'):
                archives.append(os.path.join(dirpath, name))
    return archives


def preview_bytes(data: bytes, max_len: int) -> str:
    if max_len <= 0:
        return ''
    try:
        return data[:max_len].decode('utf-8')
    except UnicodeDecodeError:
        return data[:max_len].hex()


def find_rar_exe() -> str:
    for candidate in RAR_EXE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return ''


def read_preview(rar_exe: str, archive_path: str, member_name: str, preview_len: int) -> str:
    if preview_len <= 0:
        return ''
    proc = subprocess.run(
        [rar_exe, 'p', '-inul', '-y', archive_path, member_name],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode('utf-8', errors='replace').strip() or f'rar exited {proc.returncode}')
    return preview_bytes(proc.stdout, preview_len)


def process_archive(path: str, max_entries: int, preview_len: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'path': path,
        'type': 'rar',
        'entries': [],
        'total_entries': 0
    }
    if rarfile is None:
        record['error'] = 'rarfile not installed'
        return record
    rar_exe = find_rar_exe()
    if not rar_exe:
        record['error'] = 'WinRAR Rar.exe not found'
        return record
    try:
        with rarfile.RarFile(path) as rf:
            infos = rf.infolist()
            record['total_entries'] = len(infos)
            members = infos if max_entries <= 0 else infos[:max_entries]
            for info in members:
                entry = {
                    'name': info.filename,
                    'size': info.file_size,
                    'is_dir': info.isdir()
                }
                if not info.isdir() and preview_len > 0:
                    try:
                        entry['preview'] = read_preview(rar_exe, path, info.filename, preview_len)
                    except Exception as exc:
                        entry['error'] = str(exc)
                record['entries'].append(entry)
    except Exception as exc:
        record['error'] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description='RAR 压缩包内容预览')
    parser.add_argument('--input_dir', required=True, help='待扫描目录（递归）')
    parser.add_argument('--output', required=True, help='输出报告路径 (JSON)')
    parser.add_argument('--max_entries', type=int, default=20, help='每个压缩包最多列出的文件数')
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

    print(f'[OK] ingest_archive_rar_preview completed')
    print(f"  Archives={summary['total_archives']} | errors={summary['errors']} | output={args.output}")


if __name__ == '__main__':
    main()
