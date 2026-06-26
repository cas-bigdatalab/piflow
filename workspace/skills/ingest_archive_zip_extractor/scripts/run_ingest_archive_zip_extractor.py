import argparse
import json
import os
import zipfile
from typing import Dict, Any


SPLIT_EXTENSIONS = ['.z01', '.z02', '.z03', '.z04', '.z05', '.z06', '.z07', '.z08', '.z09']


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


def find_split_parts(main_zip: str) -> list:
    base = os.path.splitext(main_zip)[0]
    dirpath = os.path.dirname(main_zip)
    prefix = os.path.basename(base)
    parts = []
    for entry in os.listdir(dirpath):
        lower = entry.lower()
        if lower.startswith(prefix.lower()) and any(lower.endswith(ext) for ext in SPLIT_EXTENSIONS):
            parts.append(os.path.join(dirpath, entry))
    return sorted(parts)


def extract_archive(path: str, output_dir: str, max_entries: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'path': path,
        'type': 'zip_split' if find_split_parts(path) else 'zip',
        'extracted': [],
        'error': None
    }
    parts = find_split_parts(path)
    merged_path = None
    try:
        if parts:
            merged_path = path + '.merged'
            with open(merged_path, 'wb') as out:
                for part in parts:
                    with open(part, 'rb') as pf:
                        out.write(pf.read())
                with open(path, 'rb') as mf:
                    out.write(mf.read())
            target = merged_path
        else:
            target = path

        with zipfile.ZipFile(target, 'r') as zf:
            members = zf.namelist()
            if max_entries > 0:
                members = members[:max_entries]
            for m in members:
                try:
                    zf.extract(m, output_dir)
                    record['extracted'].append(m)
                except Exception as exc:
                    record.setdefault('failed', []).append({'member': m, 'error': str(exc)})
    except Exception as exc:
        record['error'] = str(exc)
    finally:
        if merged_path and os.path.exists(merged_path):
            os.remove(merged_path)
    return record


def main():
    parser = argparse.ArgumentParser(description='ZIP 压缩包解压（含分卷）')
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

    print(f'[OK] ingest_archive_zip_extractor completed')
    print(f"  Archives={summary['total_archives']} | errors={summary['errors']} | report={args.report}")


if __name__ == '__main__':
    main()
