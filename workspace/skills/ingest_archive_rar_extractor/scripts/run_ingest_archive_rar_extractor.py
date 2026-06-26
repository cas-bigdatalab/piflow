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
            lower = name.lower()
            if lower.endswith('.rar') or '.part1.rar' in lower:
                archives.append(os.path.join(dirpath, name))
    return archives


def find_rar_exe() -> str:
    for candidate in RAR_EXE_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return ''


def extract_archive(path: str, output_dir: str, max_entries: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'path': path,
        'type': 'rar',
        'extracted': [],
        'error': None
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
            members = infos if max_entries <= 0 else infos[:max_entries]
            for info in members:
                try:
                    proc = subprocess.run(
                        [rar_exe, 'x', '-inul', '-y', path, info.filename, output_dir],
                        capture_output=True,
                        check=False,
                    )
                    if proc.returncode != 0:
                        raise RuntimeError(proc.stderr.decode('utf-8', errors='replace').strip() or f'rar exited {proc.returncode}')
                    record['extracted'].append(info.filename)
                except Exception as exc:
                    record.setdefault('failed', []).append({'member': info.filename, 'error': str(exc)})
    except Exception as exc:
        record['error'] = str(exc)
    return record


def main():
    parser = argparse.ArgumentParser(description='RAR 压缩包解压（含分卷）')
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

    print(f'[OK] ingest_archive_rar_extractor completed')
    print(f"  Archives={summary['total_archives']} | errors={summary['errors']} | report={args.report}")


if __name__ == '__main__':
    main()
