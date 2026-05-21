import pdfplumber
import csv
import json
from pathlib import Path

# 文件路径 - 使用绝对路径
import os
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_path = os.path.join(workspace_root, "temp", "Akcay.pdf")
output_dir = os.path.join(workspace_root, "artifacts")
outputs_dir = os.path.join(workspace_root, "outputs")

# 确保输出目录存在
Path(output_dir).mkdir(parents=True, exist_ok=True)
Path(outputs_dir).mkdir(parents=True, exist_ok=True)

# 提取所有表格数据
def extract_tables(pdf_path):
    tables_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table:
                    table_info = {
                        "page": i + 1,
                        "table_index": j + 1,
                        "data": table
                    }
                    tables_data.append(table_info)
                    print(f"Page {i+1}, Table {j+1}: {len(table)} rows")
    return tables_data

# 提取所有文本内容
def extract_text(pdf_path):
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                page_info = {
                    "page": i + 1,
                    "text": text
                }
                all_text.append(page_info)
                print(f"Page {i+1}: {len(text)} characters")
    return all_text

# 保存表格为 CSV 文件
def save_tables_to_csv(tables_data, output_dir):
    for table_info in tables_data:
        filename = f"{output_dir}/table_page{table_info['page']}_index{table_info['table_index']}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in table_info['data']:
                writer.writerow(row)
        print(f"Saved: {filename}")
    return len(tables_data)

# 生成摘要报告
def generate_summary_report(all_text, tables_data, outputs_dir):
    # 合并所有文本
    full_text = "\n\n".join([p['text'] for p in all_text])
    
    # 统计信息
    total_pages = len(all_text)
    total_tables = len(tables_data)
    total_chars = len(full_text)
    total_words = len(full_text.split())
    
    # 提取前 1000 字符作为预览
    preview = full_text[:1000] + "..." if len(full_text) > 1000 else full_text
    
    # 生成报告
    report = f"""# Akcay.pdf 摘要报告

## 基本信息
- **总页数**: {total_pages} 页
- **表格数量**: {total_tables} 个表格
- **总字符数**: {total_chars:,} 字符
- **总单词数**: {total_words:,} 单词

## 内容预览（前 1000 字符）
{preview}

## 表格提取详情
"""
    
    for table_info in tables_data:
        report += f"- 第 {table_info['page']} 页，表格 {table_info['table_index']}: {len(table_info['data'])} 行\n"
    
    # 保存报告
    report_path = f"{outputs_dir}/Akcay_摘要报告.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n摘要报告已保存：{report_path}")
    return report_path

# 执行提取
print("=" * 50)
print("开始处理 Akcay.pdf")
print("=" * 50)

print("\n【步骤 1】提取表格数据...")
tables_data = extract_tables(pdf_path)
table_count = save_tables_to_csv(tables_data, output_dir)
print(f"共提取 {table_count} 个表格")

print("\n【步骤 2】提取文本内容...")
all_text = extract_text(pdf_path)

print("\n【步骤 3】生成摘要报告...")
report_path = generate_summary_report(all_text, tables_data, outputs_dir)

print("\n" + "=" * 50)
print("处理完成！")
print("=" * 50)
