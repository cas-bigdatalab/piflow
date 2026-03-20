#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Document Deduplicator
文档级去重工具（DeepAgents + CLI 双模式）
"""

import hashlib
from collections import defaultdict
from typing import Dict, Set
import re
import os
import argparse

import pandas as pd
from datasets import Dataset


class DocumentDeduplicator:
    """
    Deduplicate documents using exact MD5 matching.
    """

    def __init__(
        self,
        text_key: str = "text",
        lowercase: bool = False,
        ignore_non_character: bool = False,
    ):
        self.text_key = text_key
        self.lowercase = lowercase

        self.remove_non_character_regex = (
            re.compile(r"\s+|\d+|[{re.escape(string.punctuation)}]")
            if ignore_non_character
            else None
        )

    def compute_hash(self, sample):

        if "hash" in sample:
            return sample

        text = sample[self.text_key]

        if self.lowercase:
            text = text.lower()

        if self.remove_non_character_regex:
            text = self.remove_non_character_regex.sub("", text)

        hash_val = hashlib.md5(text.strip().encode("utf-8")).hexdigest()

        sample["hash"] = hash_val

        return sample

    def process(self, dataset, show_num=0):

        if len(dataset) <= 1:
            return dataset, {}

        dataset = dataset.map(self.compute_hash)

        dup_hashes = None

        if show_num > 0:

            hash2ids: Dict[str, Set[int]] = defaultdict(set)

            for sid, hash_val in enumerate(dataset["hash"]):
                hash2ids[hash_val].add(sid)

            dup_samples = sorted(
                list(hash2ids.items()),
                key=lambda x: len(x[1]),
                reverse=True,
            )

            dup_hashes = set(
                [item[0] for item in dup_samples if len(item[1]) > 1][:show_num]
            )

        def _filter(sample, hashes):

            hash_val = sample["hash"]

            if hash_val in hashes:
                return False

            hashes.add(hash_val)

            return True

        hashes = set()

        dataset = dataset.filter(
            _filter,
            fn_kwargs=dict(hashes=hashes),
            load_from_cache_file=False if show_num > 0 else True,
        )

        return dataset, {}

    def save_to_csv(self, dataset, output_path):

        df = dataset.to_pandas()

        if "hash" in df.columns:
            df = df.drop("hash", axis=1)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        df.to_csv(output_path, index=False, encoding="utf-8")

        print(f"Saved dataset to {output_path}")

    def save_duplicate_pairs(self, duplicate_pairs, output_path):

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:

            for hash_val, samples in duplicate_pairs.items():

                f.write(f"Hash: {hash_val}\n")

                for i, sample in enumerate(samples):
                    f.write(f"Sample {i+1}: {sample[self.text_key][:200]}\n")

                f.write("\n")


# =========================
# DeepAgents Tool Entry
# =========================
def process1(
    input_file: str,
    output_file: str = None,
    duplicate_file: str = "duplicate_pairs.txt",
    text_key: str = "text",
    lowercase: bool = False,
    ignore_non_character: bool = False,
    show_num: int = 10,
):
    """
    Document-level deduplication tool.

    Parameters
    ----------
    input_file : 输入CSV文件
    output_file : 去重后的CSV文件
    duplicate_file : 重复样本记录文件
    text_key : 文本字段
    lowercase : 是否转小写
    ignore_non_character : 是否忽略非字母字符
    show_num : 记录重复样本数量
    """

    print(f"Reading dataset: {input_file}")

    if not os.path.exists(input_file):
        raise ValueError(f"Input file not found: {input_file}")

    df = pd.read_csv(input_file)

    dataset = Dataset.from_pandas(df)

    deduplicator = DocumentDeduplicator(
        text_key=text_key,
        lowercase=bool(lowercase),
        ignore_non_character=bool(ignore_non_character),
    )

    deduplicated_dataset, duplicate_pairs = deduplicator.process(
        dataset,
        show_num=int(show_num),
    )

    if not output_file:
        output_file = os.path.join(
            os.path.dirname(input_file),
            os.path.basename(input_file).replace(".csv", "_deduplicated.csv"),
        )

    deduplicator.save_to_csv(deduplicated_dataset, output_file)

    deduplicator.save_duplicate_pairs(duplicate_pairs, duplicate_file)

    return {
        "input_size": len(dataset),
        "output_size": len(deduplicated_dataset),
        "dedup_rate": round(
            (1 - len(deduplicated_dataset) / len(dataset)) * 100, 2
        ),
        "output_file": output_file,
        "duplicate_file": duplicate_file,
    }


# =========================
# CLI Entry
# =========================
def main():

    parser = argparse.ArgumentParser(
        description="Document-level deduplication tool"
    )

    parser.add_argument("--input_file", required=True)

    parser.add_argument("--output_file")

    parser.add_argument("--duplicate_file", default="duplicate_pairs.txt")

    parser.add_argument("--text_key", default="text")

    parser.add_argument("--lowercase", action="store_true")

    parser.add_argument("--ignore_non_character", action="store_true")

    parser.add_argument("--show_num", type=int, default=10)

    args = parser.parse_args()

    process1(
        input_file=args.input_file,
        output_file=args.output_file,
        duplicate_file=args.duplicate_file,
        text_key=args.text_key,
        lowercase=args.lowercase,
        ignore_non_character=args.ignore_non_character,
        show_num=args.show_num,
    )


if __name__ == "__main__":
    main()