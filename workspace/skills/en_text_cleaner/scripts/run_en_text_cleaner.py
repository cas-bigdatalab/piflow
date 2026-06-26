import argparse
import json
import os
import re
from typing import Any, Dict, List, Tuple, Optional


def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got '{value}'")


# 常见英文缩写词典
COMMON_ABBREVIATIONS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "haven't": "have not",
    "hasn't": "has not",
    "hadn't": "had not",
    "wouldn't": "would not",
    "shouldn't": "should not",
    "couldn't": "could not",
    "mightn't": "might not",
    "mustn't": "must not",
    "shan't": "shall not",
    "let's": "let us",
    "that's": "that is",
    "who's": "who is",
    "what's": "what is",
    "here's": "here is",
    "there's": "there is",
    "where's": "where is",
    "how's": "how is",
    "it's": "it is",
    "he's": "he is",
    "she's": "she is",
    "they're": "they are",
    "we're": "we are",
    "you're": "you are",
    "i'm": "i am",
    "i've": "i have",
    "you've": "you have",
    "we've": "we have",
    "they've": "they have",
    "i'll": "i will",
    "you'll": "you will",
    "he'll": "he will",
    "she'll": "she will",
    "it'll": "it will",
    "we'll": "we will",
    "they'll": "they will",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "dr.": "doctor",
    "mr.": "mister",
    "mrs.": "missus",
    "ms.": "miss",
    "prof.": "professor",
    "dept.": "department",
    "univ.": "university",
    "est.": "estimated",
    "approx.": "approximately",
    "etc.": "et cetera",
    "et al.": "et alii",
    "e.g.": "for example",
    "i.e.": "that is",
    "vs.": "versus",
    "vol.": "volume",
    "vols.": "volumes",
    "ed.": "edition",
    "eds.": "editors",
    "fig.": "figure",
    "figs.": "figures",
    "no.": "number",
    "nos.": "numbers",
    "p.": "page",
    "pp.": "pages",
    "sec.": "section",
    "secs.": "sections",
    "ch.": "chapter",
    "chs.": "chapters",
    "pt.": "part",
    "pts.": "parts",
    "abt.": "about",
    "amt.": "amount",
    "w/": "with",
    "w/o": "without",
    "b/c": "because",
    "b/c": "because",
    "b/t": "between",
    "r/u": "are you",
    "y/o": "years old",
}

# 常见拼写错误词典（简化版）
COMMON_MISSPELLINGS = {
    "accomodate": "accommodate",
    "acheive": "achieve",
    "across": "across",
    "agressive": "aggressive",
    "apparantly": "apparently",
    "appearence": "appearance",
    "arguement": "argument",
    "beleive": "believe",
    "calender": "calendar",
    "catagory": "category",
    "cemetary": "cemetery",
    "changeable": "changeable",
    "collectable": "collectible",
    "column": "column",
    "comming": "coming",
    "committed": "committed",
    "conceed": "concede",
    "concious": "conscious",
    "contraversy": "controversy",
    "cooly": "coolly",
    "dacquiri": "daiquiri",
    "decieve": "deceive",
    "definate": "definite",
    "definately": "definitely",
    "desparate": "desperate",
    "dilema": "dilemma",
    "disapoint": "disappoint",
    "dissapoint": "disappoint",
    "embarass": "embarrass",
    "equipement": "equipment",
    "excede": "exceed",
    "exellent": "excellent",
    "experiance": "experience",
    "extreem": "extreme",
    "facinate": "fascinate",
    "facinating": "fascinating",
    "finaly": "finally",
    "foriegn": "foreign",
    "fourty": "forty",
    "goverment": "government",
    "grammer": "grammar",
    "harrass": "harass",
    "hieght": "height",
    "hipocrit": "hypocrite",
    "humerous": "humorous",
    "imediately": "immediately",
    "incidently": "incidentally",
    "independant": "independent",
    "indispensible": "indispensable",
    "intresting": "interesting",
    "knowlege": "knowledge",
    "liason": "liaison",
    "lightening": "lightning",
    "loose": "lose",
    "maintainance": "maintenance",
    "maintnance": "maintenance",
    "medevil": "medieval",
    "mispell": "misspell",
    "neccessary": "necessary",
    "necesserily": "necessarily",
    "neice": "niece",
    "noticable": "noticeable",
    "noticably": "noticeably",
    "occurence": "occurrence",
    "occured": "occurred",
    "occuring": "occurring",
    "paralell": "parallel",
    "pasttime": "pastime",
    "peice": "piece",
    "playwrite": "playwright",
    "posession": "possession",
    "prefered": "preferred",
    "prefering": "preferring",
    "proceedure": "procedure",
    "publically": "publicly",
    "realy": "really",
    "recieve": "receive",
    "refered": "referred",
    "refering": "referring",
    "religous": "religious",
    "repetion": "repetition",
    "restaraunt": "restaurant",
    "rythm": "rhythm",
    "sieze": "seize",
    "sentance": "sentence",
    "seperate": "separate",
    "sieze": "seize",
    "similer": "similar",
    "speach": "speech",
    "stoping": "stopping",
    "sucess": "success",
    "supercede": "supersede",
    "suprise": "surprise",
    "tommorow": "tomorrow",
    "tommorrow": "tomorrow",
    "truely": "truly",
    "untill": "until",
    "unuseable": "unusable",
    "useable": "usable",
    "weild": "wield",
    "weird": "weird",
    "whereever": "wherever",
    "wich": "which",
    "wierd": "weird",
    "yourslef": "yourself",
}


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """加载JSONL文件"""
    if not os.path.exists(path):
        return []
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError:
                items.append({"_raw": line, "_parse_error": True})
    return items


def save_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    """保存JSONL文件"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def expand_abbreviations(text: str, abbrev_dict: Dict[str, str]) -> Tuple[str, int, List[Dict[str, Any]]]:
    """
    展开缩写
    返回: (展开后文本, 替换次数, 替换明细)
    """
    count = 0
    result = text
    details: List[Dict[str, Any]] = []
    # 按长度降序排序，优先替换长的
    sorted_abbrs = sorted(abbrev_dict.items(), key=lambda x: len(x[0]), reverse=True)

    for abbr, full in sorted_abbrs:
        # 兼容带标点的缩写，如 e.g. / prof. / w/
        escaped = re.escape(abbr)
        if re.match(r'^[\w]+[./]?$|^[\w]+/[\w]+$', abbr.lower()):
            pattern = r'(?<!\w)' + escaped + r'(?!\w)'
        else:
            pattern = r'\b' + escaped + r'\b'
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            pieces = []
            last_end = 0
            for match in matches:
                matched = match.group(0)
                if matched.isupper():
                    replaced = full.upper()
                elif matched[0].isupper():
                    replaced = full.capitalize()
                else:
                    replaced = full.lower()
                pieces.append(result[last_end:match.start()])
                pieces.append(replaced)
                last_end = match.end()
                count += 1
                details.append({
                    "type": "abbreviation",
                    "original": matched,
                    "cleaned": replaced,
                    "count": 1
                })
            pieces.append(result[last_end:])
            result = ''.join(pieces)

    return result, count, details


def correct_spelling(text: str, spell_dict: Dict[str, str]) -> Tuple[str, int, List[Dict[str, Any]]]:
    """
    纠正拼写错误
    返回: (纠正后文本, 纠正次数, 纠正明细)
    """
    count = 0
    details: List[Dict[str, Any]] = []
    words = re.findall(r'\b[a-zA-Z]+\b', text)

    result = text
    for word in set(words):
        lower_word = word.lower()
        if lower_word in spell_dict:
            correct = spell_dict[lower_word]
            # 保持原始大小写
            if word.isupper():
                correct = correct.upper()
            elif word[0].isupper():
                correct = correct.capitalize()
            result = re.sub(r'\b' + re.escape(word) + r'\b', correct, result)
            count += 1
            details.append({
                "type": "spelling",
                "original": word,
                "cleaned": correct,
                "count": 1
            })

    return result, count, details


def normalize_case(text: str) -> str:
    """
    统一大小写：句子首字母大写，其余小写
    """
    sentences = re.split(r'([.!?]+\s+)', text)
    result = []
    
    for i, sent in enumerate(sentences):
        if i % 2 == 0:  # 句子内容
            sent = sent.strip().lower()
            if sent:
                sent = sent[0].upper() + sent[1:] if len(sent) > 1 else sent.upper()
            result.append(sent)
        else:  # 分隔符
            result.append(sent)
    
    return ''.join(result)


def process(args: argparse.Namespace) -> Dict[str, Any]:
    """处理主函数"""
    data = load_jsonl(args.input)
    
    processed_count = 0
    total_abbr_expanded = 0
    total_spelling_fixed = 0
    
    results = []
    
    # 加载自定义缩写词典
    abbrev_dict = COMMON_ABBREVIATIONS.copy()
    if args.custom_abbreviations:
        try:
            with open(args.custom_abbreviations, "r", encoding="utf-8") as f:
                custom = json.load(f)
                abbrev_dict.update(custom)
        except Exception as e:
            print(f"[WARN] Failed to load custom abbreviations: {e}")
    
    # 加载自定义拼写词典
    spell_dict = COMMON_MISSPELLINGS.copy()
    if args.custom_spellings:
        try:
            with open(args.custom_spellings, "r", encoding="utf-8") as f:
                custom = json.load(f)
                spell_dict.update(custom)
        except Exception as e:
            print(f"[WARN] Failed to load custom spellings: {e}")
    
    for item in data:
        text = str(item.get(args.text_field, ""))
        if not text:
            results.append(item)
            continue
        
        original_text = text
        changes = {}
        change_details = []

        # 展开缩写
        if args.expand_abbreviations:
            text, abbr_count, abbr_details = expand_abbreviations(text, abbrev_dict)
            if abbr_count > 0:
                changes["abbreviations_expanded"] = abbr_count
                total_abbr_expanded += abbr_count
                change_details.extend(abbr_details)

        # 纠正拼写
        if args.fix_spelling:
            text, spell_count, spell_details = correct_spelling(text, spell_dict)
            if spell_count > 0:
                changes["spelling_fixed"] = spell_count
                total_spelling_fixed += spell_count
                change_details.extend(spell_details)
        
        # 规范化大小写
        if args.normalize_case:
            text = normalize_case(text)
            changes["case_normalized"] = True
        
        # 标记修改
        if changes:
            processed_count += 1
            new_item = item.copy()
            new_item[args.text_field] = text
            if args.mark_cleaned:
                new_item["_en_cleaned"] = True
                new_item["_changes"] = changes
                new_item["_en_change_details"] = change_details
            results.append(new_item)
        else:
            results.append(item)
    
    # 保存结果
    save_jsonl(args.output, results)
    
    print("[OK] English text cleaning completed")
    print(f"   Input: {args.input}")
    print(f"   Output: {args.output}")
    print(f"   Total samples: {len(data)}")
    print(f"   Samples processed: {processed_count}")
    print(f"   Abbreviations expanded: {total_abbr_expanded}")
    print(f"   Spelling fixed: {total_spelling_fixed}")
    
    return {
        "input": args.input,
        "output": args.output,
        "total_samples": len(data),
        "processed_samples": processed_count,
        "abbreviations_expanded": total_abbr_expanded,
        "spelling_fixed": total_spelling_fixed
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="English text cleaner - 英文文本清洗优化")
    parser.add_argument("--input", required=True, help="输入JSONL文件路径")
    parser.add_argument("--output", required=True, help="输出JSONL文件路径")
    parser.add_argument("--text_field", default="text", help="文本字段名，默认text")
    parser.add_argument("--expand_abbreviations", type=str_to_bool, default=True, help="展开缩写，默认True")
    parser.add_argument("--fix_spelling", type=str_to_bool, default=True, help="纠正拼写，默认True")
    parser.add_argument("--normalize_case", type=str_to_bool, default=False, help="规范化大小写，默认False")
    parser.add_argument("--mark_cleaned", type=str_to_bool, default=True, help="标记已清洗样本，默认True")
    parser.add_argument("--custom_abbreviations", default="", help="自定义缩写词典JSON文件路径")
    parser.add_argument("--custom_spellings", default="", help="自定义拼写词典JSON文件路径")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    process(args)


if __name__ == "__main__":
    main()
