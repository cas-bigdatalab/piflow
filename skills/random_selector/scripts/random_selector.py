#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RandomSelector: 从数据集中随机选择样本
"""

import argparse
import pandas as pd
from datasets import Dataset
import numpy as np
from pathlib import Path


def random_sample(dataset, weight=1.0, sample_number=0, seed=None):
    """
    Randomly sample a subset from a dataset with weight or number.

    :param dataset: HuggingFace dataset
    :param weight: sample ratio
    :param sample_number: fixed sample number
    :param seed: random seed
    """

    if seed is None:
        seed = 42

    ds_samples = len(dataset)

    if sample_number <= 0:
        sample_number = int(np.ceil(ds_samples * weight))

    if sample_number == ds_samples:
        return dataset

    sample_index = range(sample_number)

    n_repeat = int(np.ceil(sample_number / ds_samples)) - 1

    if n_repeat > 0:

        remain_samples = sample_number - n_repeat * ds_samples

        from itertools import chain, repeat

        sample_index = chain(
            *repeat(range(ds_samples), n_repeat),
            range(remain_samples)
        )

    return dataset.shuffle(seed=seed).select(sample_index)


def process(input_file, output_file, select_ratio=None, select_num=None, seed=None):
    """
    Process dataset random sampling.

    :param input_file: CSV path
    :param output_file: CSV path
    :param select_ratio: sample ratio
    :param select_num: sample number
    :param seed: random seed
    """

    # -------------------------
    # 参数类型转换（解决 Agent 字符串问题）
    # -------------------------

    if select_ratio is not None:
        try:
            select_ratio = float(select_ratio)
        except Exception:
            raise ValueError("select_ratio must be numeric")

    if select_num is not None:
        try:
            select_num = int(select_num)
        except Exception:
            raise ValueError("select_num must be integer")

    if seed is not None:
        seed = int(seed)

    # -------------------------
    # 参数校验
    # -------------------------

    if select_ratio is not None:
        if not 0 <= select_ratio <= 1:
            raise ValueError("select_ratio must be between 0 and 1")

    if select_num is not None:
        if select_num < 0:
            raise ValueError("select_num must be non-negative")

    # -------------------------
    # 读取数据
    # -------------------------

    print(f"Reading input file: {input_file}")

    df = pd.read_csv(input_file)

    print(f"Original dataset size: {len(df)}")

    dataset = Dataset.from_pandas(df)

    # -------------------------
    # 数据过小
    # -------------------------

    if len(dataset) <= 1:

        print("Dataset too small, returning original")

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_file, index=False, encoding="utf-8")

        return f"Dataset too small. Saved original to {output_file}"

    # -------------------------
    # 未提供参数
    # -------------------------

    if select_ratio is None and select_num is None:

        print("No selection parameters provided")

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_file, index=False, encoding="utf-8")

        return f"No sampling applied. Saved original to {output_file}"

    # -------------------------
    # 计算样本数量
    # -------------------------

    if select_ratio is None:

        select_number = select_num

    else:

        select_number = int(select_ratio * len(dataset))

        if select_num is not None and select_num < select_number:
            select_number = select_num

    print(f"Selecting {select_number} samples")

    # -------------------------
    # 执行采样
    # -------------------------

    sampled_dataset = random_sample(
        dataset,
        sample_number=select_number,
        seed=seed
    )

    sampled_df = sampled_dataset.to_pandas()

    print(f"Sampled dataset size: {len(sampled_df)}")

    # -------------------------
    # 保存结果
    # -------------------------

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    sampled_df.to_csv(
        output_file,
        index=False,
        encoding="utf-8"
    )

    print(f"Output saved to: {output_file}")

    return {
        "input_size": len(df),
        "sampled_size": len(sampled_df),
        "output_file": output_file
    }


def main():

    parser = argparse.ArgumentParser(
        description="Randomly select samples from a dataset"
    )

    parser.add_argument(
        "--input_file",
        type=str,
        required=True,
        help="Input CSV file path"
    )

    parser.add_argument(
        "--output_file",
        type=str,
        required=True,
        help="Output CSV file path"
    )

    parser.add_argument(
        "--select_ratio",
        type=float,
        default=None,
        help="Selection ratio (0-1)"
    )

    parser.add_argument(
        "--select_num",
        type=int,
        default=None,
        help="Selection number"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed"
    )

    args = parser.parse_args()

    process(
        args.input_file,
        args.output_file,
        args.select_ratio,
        args.select_num,
        args.seed
    )


if __name__ == "__main__":
    main()