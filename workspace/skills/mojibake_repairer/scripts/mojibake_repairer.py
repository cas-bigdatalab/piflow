import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

CURRENT_DIR = Path(__file__).resolve().parent
from data_io import read_structured_data, write_structured_data  # type: ignore  # noqa: E402

# ── 自动检测编码修复链 ─────────────────────────────────────────────────
# 仅包含 src_encoding→utf-8 方向（修复编码错误为正确的 UTF-8）
# utf-8→X 方向容易产生误报，请通过 --chain 手动指定
AUTO_CHAINS = [
    ("gbk", "utf-8"),
    ("gb2312", "utf-8"),
    ("gb18030", "utf-8"),
    ("big5", "utf-8"),
    ("shift_jis", "utf-8"),
    ("euc_kr", "utf-8"),
    ("euc_jp", "utf-8"),
    ("latin-1", "utf-8"),
    ("cp1252", "utf-8"),
    ("cp1250", "utf-8"),
    ("cp1251", "utf-8"),
]

MOJIBAKE_MARKER_RE = re.compile(
    r"(锟|�|Ã|Â|â€|Ð|Ñ|浣犲|涓|鏄|鐨|锛|骞|鏈|绗|鍙|榛)"
)

# 字符合理度：可读字符正则（字母、数字、CJK、标点、空白）
_PLAUSIBLE_RE = re.compile(
    r"[\w\d\s"
    r"一-鿿"     # CJK 统一表意文字
    r"　-〿"     # CJK 标点
    r"＀-￯"     # 全角/半角
    r"぀-ゟ"     # 日文平假名
    r"゠-ヿ"     # 日文片假名
    r"가-힯"     # 韩文
    r"Ѐ-ӿ"     # 西里尔字母
    r"À-ÿ"     # Latin-1 补充（带重音字母）
    r"Ā-ɏ"     # Latin 扩展
    r"\.\,\!\?\:\;\-\(\)\[\]\{\}\"\'"
    r"\@\#\$\%\^\&\*\+\/\<\>\=\~"
    r"]",
    re.UNICODE,
)


def _score_text(text: str) -> float:
    """计算字符合理度评分 (0~1)，编码失败产物 (? 和 �) 扣分"""
    if not text:
        return 1.0
    total = len(text)
    # 编码/解码失败产物
    artifact_count = text.count("?") + text.count("�")
    if artifact_count > total * 0.3:
        return 0.0
    plausible = len(_PLAUSIBLE_RE.findall(text))
    score = (plausible - artifact_count) / total
    return max(0.0, score)


def _looks_like_mojibake(text: str) -> bool:
    return bool(MOJIBAKE_MARKER_RE.search(text))


def _try_chain(text: str, src_enc: str, dst_enc: str) -> Optional[Tuple[str, float]]:
    """尝试用指定编码链修复，返回 (修复文本, 评分) 或 None"""
    try:
        encoded = text.encode(src_enc, errors="strict")
    except UnicodeEncodeError:
        return None

    try:
        repaired = encoded.decode(dst_enc, errors="strict")
    except UnicodeDecodeError:
        return None

    # 替换字符 ? (编码失败) 和 � (解码失败) 过多 → 拒绝
    loss = repaired.count("?") + repaired.count("�")
    if loss > len(repaired) * 0.15:
        return None

    score = _score_text(repaired)
    return repaired, score


def _auto_repair(text: str, min_score: float) -> Tuple[str, float, str]:
    """自动尝试所有编码链，返回 (最佳文本, 评分, 使用的链)"""
    best_text = text
    best_score = _score_text(text)
    best_chain = "无（原文）"
    original_looks_broken = _looks_like_mojibake(text)

    for src, dst in AUTO_CHAINS:
        result = _try_chain(text, src, dst)
        if result is None:
            continue
        repaired, score = result
        improves_score = score > best_score + 0.05
        fixes_suspect_text = original_looks_broken and score >= best_score - 0.02
        if (improves_score or fixes_suspect_text) and repaired != text:
            best_text = repaired
            best_score = score
            best_chain = f"{src}→{dst}"

    if best_score < min_score or best_text == text:
        return text, best_score, f"无（评分 {best_score:.2f}，无需修复）"
    return best_text, best_score, best_chain


def _repair_with_chain(text: str, chain_str: str) -> Tuple[str, float, str]:
    """用指定编码链修复"""
    parts = chain_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"编码链格式应为 src:dst，收到: {chain_str}")
    src, dst = parts[0].strip(), parts[1].strip()
    result = _try_chain(text, src, dst)
    if result is None:
        return text, 0.0, f"{src}→{dst}（失败）"
    repaired, score = result
    return repaired, score, f"{src}→{dst}"


def _select_columns(df: pd.DataFrame, text_columns: Optional[str]) -> List[str]:
    if text_columns:
        requested = [c.strip() for c in text_columns.split(",") if c.strip()]
        missing = [c for c in requested if c not in df.columns]
        if missing:
            print(f"[WARN] 未找到的列将被忽略: {missing}")
        return [c for c in requested if c in df.columns]
    return [col for col in df.columns if df[col].dtype == "object"]


def repair_mojibake(
    df: pd.DataFrame,
    cols: List[str],
    min_score: float,
    chain: Optional[str],
) -> pd.DataFrame:
    result = df.copy()
    repair_log: List[str] = []

    for col in cols:
        for idx in df.index:
            val = df.at[idx, col]
            if pd.isna(val):
                continue
            text = str(val)

            if chain:
                repaired, score, chain_label = _repair_with_chain(text, chain)
            else:
                repaired, score, chain_label = _auto_repair(text, min_score)

            if repaired != text:
                result.at[idx, col] = repaired
                preview_src = text[:40].replace("\n", "\\n")
                preview_dst = repaired[:40].replace("\n", "\\n")
                repair_log.append(
                    f"  [{col}][行{idx}] {chain_label} (score={score:.2f})\n"
                    f"    {preview_src} → {preview_dst}"
                )

    if repair_log:
        print(f"[REPAIR] 共修复 {len(repair_log)} 处乱码:")
        for entry in repair_log[:20]:  # 最多显示前20条
            print(entry)
        if len(repair_log) > 20:
            print(f"  ... 还有 {len(repair_log) - 20} 条修复记录")
    else:
        print("[REPAIR] 未检测到需要修复的乱码")

    return result


def run_repairer(
    input_path: str,
    output_path: str,
    text_columns: Optional[str],
    min_score: float,
    chain: Optional[str],
):
    df = read_structured_data(input_path)
    cols = _select_columns(df, text_columns)
    if not cols:
        print("[WARN] 未选中文本列，默认全字符串列。")
        cols = _select_columns(df, None)

    repaired = repair_mojibake(df, cols=cols, min_score=min_score, chain=chain)
    write_structured_data(repaired, output_path)

    mode = f"手动链 {chain}" if chain else "自动检测"
    print(f"[OK] 乱码修复完成 -> {output_path}  (模式={mode}, min_score={min_score})")


def main():
    parser = argparse.ArgumentParser(
        description="乱码修复器：自动检测并修复编码错解释导致的乱码（Mojibake）"
    )
    parser.add_argument("--input_path", required=True, help="输入文件路径")
    parser.add_argument("--output_path", required=True, help="输出文件路径")
    parser.add_argument(
        "--text_columns",
        required=False,
        default=None,
        help="处理的文本列，逗号分隔；默认全部字符串列",
    )
    parser.add_argument(
        "--min_score",
        required=False,
        type=float,
        default=0.6,
        help="最小修复评分阈值 0~1（默认 0.6），低于此值不替换原文",
    )
    parser.add_argument(
        "--chain",
        required=False,
        default=None,
        help="手动指定编码修复链，如 gbk:utf-8；不指定则自动检测",
    )

    args = parser.parse_args()
    run_repairer(
        input_path=args.input_path,
        output_path=args.output_path,
        text_columns=args.text_columns,
        min_score=args.min_score,
        chain=args.chain,
    )


if __name__ == "__main__":
    main()
