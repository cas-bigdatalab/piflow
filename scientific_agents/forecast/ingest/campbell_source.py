"""Read-only incremental collection from the station's local directory."""
from pathlib import Path


def collect(directory, known):
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Source is not a directory")
    signatures, changed = {}, {}
    for path in sorted(root.glob("????-??-??/*.jsonl")):
        if root not in path.resolve().parents:
            raise ValueError("Source file escapes station directory")
        name = path.relative_to(root).as_posix()
        before = path.stat()
        signature = [before.st_size, before.st_mtime_ns]
        signatures[name] = signature
        if known.get(name) == signature:
            continue
        content = path.read_bytes()
        after = path.stat()
        if signature != [after.st_size, after.st_mtime_ns] or len(content) != before.st_size:
            raise ValueError("Source changed during scan; retry: " + name)
        changed[name] = content.decode("utf-8-sig")
    if not signatures:
        raise ValueError("No daily JSONL files found in station directory")
    return {"signatures": signatures, "changed": changed}
