import argparse
import fcntl
import gzip
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any


CHINESE_RE = re.compile(r"[㐀-䶿一-鿿\U00020000-\U0002FA1F]")
ENGLISH_RE = re.compile(r"[A-Za-z]")
COMMON_ABBREVIATIONS = {
    "e.g.", "i.e.", "etc.", "fig.", "eq.", "ref.", "dr.", "mr.", "mrs.", "prof.",
}

MODEL_FILENAME = "model_quantized.onnx"
MODEL_SIZE = 118308126
MODEL_SHA256 = "66fc00f5f29afcaff34092e1bdd20008ca3918265a82fb9695a551e510cc4ebc"
MODEL_ARCHIVE_NAME = f"{MODEL_FILENAME}.gz"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def model_is_ready(model_path: Path) -> bool:
    return (
        model_path.is_file()
        and model_path.stat().st_size == MODEL_SIZE
        and file_sha256(model_path) == MODEL_SHA256
    )


def extract_model_archive(model_path: Path) -> None:
    onnx_dir = model_path.parent
    archive_path = onnx_dir / MODEL_ARCHIVE_NAME
    temporary_model = onnx_dir / f".{MODEL_FILENAME}.extracting"

    if not archive_path.is_file():
        raise RuntimeError(f"预置 INT8 ONNX 模型及压缩包均不存在: {archive_path}")
    with archive_path.open("rb") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if model_is_ready(model_path):
            return
        try:
            temporary_model.unlink(missing_ok=True)
            with gzip.open(archive_path, "rb") as source, temporary_model.open(
                "wb"
            ) as destination:
                shutil.copyfileobj(source, destination)
            if not model_is_ready(temporary_model):
                raise RuntimeError("模型解压后的 ONNX 文件大小或 SHA-256 不匹配")
            os.replace(temporary_model, model_path)
        except (EOFError, OSError) as error:
            raise RuntimeError(f"模型解压失败: {error}") from error
        finally:
            temporary_model.unlink(missing_ok=True)


def split_units(text: str) -> list[tuple[str, int, int]]:
    units: list[tuple[str, int, int]] = []
    start = 0
    index = 0
    while index < len(text):
        character = text[index]
        boundary = character in "。！？!?；;\n"
        if character == ".":
            next_index = index + 1
            while next_index < len(text) and text[next_index] in " \t":
                next_index += 1
            preceding = text[start:index + 1].strip().lower()
            last_token = preceding.split()[-1] if preceding.split() else ""
            next_character = text[next_index] if next_index < len(text) else ""
            boundary = (
                next_index == len(text)
                or next_character == "\n"
                or next_character.isupper()
                or next_character.isdigit()
                or bool(CHINESE_RE.match(next_character))
            ) and last_token not in COMMON_ABBREVIATIONS and not (
                len(last_token) == 2 and last_token[0].islower() and last_token.endswith(".")
            )
        if boundary:
            end = index if character == "\n" else index + 1
            unit_start = start
            while unit_start < end and text[unit_start].isspace():
                unit_start += 1
            unit_end = end
            while unit_end > unit_start and text[unit_end - 1].isspace():
                unit_end -= 1
            if unit_start < unit_end:
                units.append((text[unit_start:unit_end], unit_start, unit_end))
            start = index + 1
        index += 1
    unit_start = start
    while unit_start < len(text) and text[unit_start].isspace():
        unit_start += 1
    unit_end = len(text)
    while unit_end > unit_start and text[unit_end - 1].isspace():
        unit_end -= 1
    if unit_start < unit_end:
        units.append((text[unit_start:unit_end], unit_start, unit_end))
    return units


def detect_language(unit: str) -> str | None:
    chinese_count = len(CHINESE_RE.findall(unit))
    english_count = len(ENGLISH_RE.findall(unit))
    if chinese_count == 0 and english_count == 0:
        return None
    return "zh" if chinese_count >= english_count else "en"


def cosine_similarity(left, right) -> float:
    return float(left @ right / ((left @ left) ** 0.5 * (right @ right) ** 0.5))


class OnnxInt8Embedder:
    def __init__(self):
        try:
            import numpy as np
            import onnxruntime as ort
            from transformers import PreTrainedTokenizerFast
        except ImportError as error:
            raise RuntimeError(
                "缺少 ONNX INT8 推理依赖，请先安装：pip install numpy onnxruntime transformers"
            ) from error

        self.np = np
        assets_dir = Path(__file__).resolve().parent / "assets"
        model_path = assets_dir / "onnx" / MODEL_FILENAME
        tokenizer_path = assets_dir / "tokenizer.json"
        if not model_is_ready(model_path):
            extract_model_archive(model_path)
        if not tokenizer_path.is_file():
            raise FileNotFoundError(f"未找到预置模型分词器文件: {tokenizer_path}")
        self.tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        self.input_names = {item.name for item in self.session.get_inputs()}

    def encode(self, texts: list[str]):
        encoded = self.tokenizer(texts, padding=True, truncation=True, return_tensors="np")
        inputs = {
            name: value.astype(self.np.int64)
            for name, value in encoded.items()
            if name in self.input_names
        }
        if "token_type_ids" in self.input_names and "token_type_ids" not in inputs:
            inputs["token_type_ids"] = self.np.zeros_like(inputs["input_ids"])
        outputs = self.session.run(None, inputs)
        token_embeddings = outputs[0]
        attention_mask = encoded["attention_mask"].astype(self.np.float32)[..., None]
        pooled = (token_embeddings * attention_mask).sum(axis=1) / self.np.clip(
            attention_mask.sum(axis=1), 1e-9, None
        )
        return pooled / self.np.clip(self.np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12, None)


def find_duplicate_pairs(units: list[str], threshold: float, model: OnnxInt8Embedder) -> list[tuple[int, int, float]]:
    languages = [detect_language(unit) for unit in units]
    chinese_indexes = [index for index, language in enumerate(languages) if language == "zh"]
    english_indexes = [index for index, language in enumerate(languages) if language == "en"]
    if not chinese_indexes or not english_indexes:
        return []

    embeddings = model.encode(units)
    candidates: list[tuple[float, int, int]] = []
    for chinese_index in chinese_indexes:
        for english_index in english_indexes:
            score = cosine_similarity(embeddings[chinese_index], embeddings[english_index])
            if score >= threshold:
                candidates.append((score, chinese_index, english_index))

    matched: set[int] = set()
    pairs: list[tuple[int, int, float]] = []
    for score, chinese_index, english_index in sorted(candidates, reverse=True):
        if chinese_index in matched or english_index in matched:
            continue
        matched.update((chinese_index, english_index))
        pairs.append((chinese_index, english_index, score))
    return pairs


def deduplicate_text(text: str, threshold: float, keep: str, model: OnnxInt8Embedder) -> tuple[str, int, int, int]:
    positioned_units = split_units(text)
    units = [unit for unit, _, _ in positioned_units]
    pairs = find_duplicate_pairs(units, threshold, model)
    remove_indexes: set[int] = set()
    for chinese_index, english_index, _ in pairs:
        remove_indexes.add(english_index if keep == "zh" else chinese_index)
    chinese_count = sum(detect_language(unit) == "zh" for unit in units)
    english_count = sum(detect_language(unit) == "en" for unit in units)
    if not remove_indexes:
        return text, 0, chinese_count, english_count

    ranges: list[tuple[int, int]] = []
    for index in sorted(remove_indexes):
        _, start, end = positioned_units[index]
        while end < len(text) and text[end] in " \t":
            end += 1
        if end < len(text) and text[end] == "\r":
            end += 1
        if end < len(text) and text[end] == "\n":
            end += 1
        ranges.append((start, end))

    result: list[str] = []
    cursor = 0
    for start, end in ranges:
        result.append(text[cursor:start])
        cursor = end
    result.append(text[cursor:])
    cleaned = "".join(result)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned, len(remove_indexes), chinese_count, english_count


def process_json_value(
    value: Any,
    text_key: str,
    threshold: float,
    keep: str,
    model: OnnxInt8Embedder,
) -> tuple[Any, dict[str, int]]:
    stats = {"documents": 0, "removed": 0, "chinese": 0, "english": 0}
    if isinstance(value, dict):
        result = dict(value)
        if isinstance(result.get(text_key), str):
            cleaned, removed, chinese, english = deduplicate_text(
                result[text_key], threshold, keep, model
            )
            result[text_key] = cleaned
            stats = {"documents": 1, "removed": removed, "chinese": chinese, "english": english}
        return result, stats
    if isinstance(value, list):
        result = []
        for item in value:
            cleaned, item_stats = process_json_value(item, text_key, threshold, keep, model)
            result.append(cleaned)
            for key in stats:
                stats[key] += item_stats[key]
        return result, stats
    if isinstance(value, str):
        cleaned, removed, chinese, english = deduplicate_text(value, threshold, keep, model)
        return cleaned, {"documents": 1, "removed": removed, "chinese": chinese, "english": english}
    return value, stats


def process_file(
    input_path: Path,
    output_path: Path,
    text_key: str,
    threshold: float,
    keep: str,
    model: OnnxInt8Embedder,
) -> dict[str, int]:
    suffix = input_path.suffix.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if suffix == ".txt":
        source = input_path.read_text(encoding="utf-8")
        cleaned, removed, chinese, english = deduplicate_text(source, threshold, keep, model)
        output_path.write_text(cleaned, encoding="utf-8")
        return {"documents": 1, "removed": removed, "chinese": chinese, "english": english}

    if suffix == ".json":
        with input_path.open("r", encoding="utf-8") as handle:
            source = json.load(handle)
        cleaned, stats = process_json_value(source, text_key, threshold, keep, model)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(cleaned, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return stats

    if suffix == ".jsonl":
        stats = {"documents": 0, "removed": 0, "chinese": 0, "english": 0}
        with input_path.open("r", encoding="utf-8") as source, output_path.open(
            "w", encoding="utf-8"
        ) as destination:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    destination.write(line)
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"第 {line_number} 行不是有效 JSON") from error
                cleaned, record_stats = process_json_value(record, text_key, threshold, keep, model)
                destination.write(json.dumps(cleaned, ensure_ascii=False) + "\n")
                for key in stats:
                    stats[key] += record_stats[key]
        return stats

    raise ValueError("输入文件仅支持 .txt、.json 或 .jsonl 格式")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="中英文混杂 ONNX INT8 句段语义去重")
    parser.add_argument("--input", required=True, help="输入 TXT、JSON 或 JSONL 文档路径")
    parser.add_argument("--output", required=True, help="输出 TXT、JSON 或 JSONL 文档路径")
    parser.add_argument(
        "--text_key",
        default="text",
        help="JSON/JSONL 中待去重正文所在的字段名称；TXT 输入不使用此参数",
    )
    parser.add_argument(
        "--similarity_threshold",
        type=float,
        default=0.75,
        help="跨语种语义重复阈值，范围为 0 到 1",
    )
    parser.add_argument(
        "--keep",
        choices=["zh", "en"],
        default="zh",
        help="重复句段保留语种，可选 zh 或 en",
    )
    args = parser.parse_args()
    if not 0 <= args.similarity_threshold <= 1:
        parser.error("--similarity_threshold 必须在 0 到 1 之间")
    if Path(args.input).suffix.lower() != Path(args.output).suffix.lower():
        parser.error("输入和输出文件扩展名必须一致")
    return args


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_file():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")
    model = OnnxInt8Embedder()
    stats = process_file(
        input_path,
        Path(args.output),
        args.text_key,
        args.similarity_threshold,
        args.keep,
        model,
    )
    print("[OK] 中英文 ONNX INT8 去重完成")
    print(f"处理文档数: {stats['documents']}")
    print(f"中文句段数: {stats['chinese']}")
    print(f"英文句段数: {stats['english']}")
    print(f"已删除跨语种重复句段数: {stats['removed']}")
    print(f"输出文件: {args.output}")


if __name__ == "__main__":
    main()
