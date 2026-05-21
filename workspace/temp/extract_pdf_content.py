#!/usr/bin/env python3
"""
提取 PDF 文件中的表格和文本内容
"""

import pdfplumber
import pandas as pd
import os

# 输入文件路径
input_pdf = "/temp/Akcay.pdf"
output_dir = "/artifacts"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

print(f"正在处理 PDF 文件：{input_pdf}")

# 打开 PDF
with pdfplumber.open(input_pdf) as pdf:
    print(f"PDF 总页数：{len(pdf.pages)}")
    
    # ========== 提取表格 ==========
    print("\n=== 提取表格数据 ===")
    all_tables = []
    table_info = []
    
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            for j, table in enumerate(tables):
                if table and len(table) > 1:  # 确保表格不为空且有数据
                    # 使用第一行作为表头
                    header = table[0]
                    # 清理表头（去除 None 值）
                    header = [str(h) if h is not None else f"Column_{k}" for k, h in enumerate(header)]
                    
                    # 创建 DataFrame
                    df = pd.DataFrame(table[1:], columns=header)
                    
                    # 添加表格信息
                    table_identifier = f"Page{i+1}_Table{j+1}"
                    df.insert(0, 'Source', table_identifier)
                    
                    all_tables.append(df)
                    table_info.append({
                        'page': i + 1,
                        'table_num': j + 1,
                        'rows': len(table) - 1,
                        'cols': len(header)
                    })
                    print(f"  页面 {i+1}, 表格 {j+1}: {len(table)-1} 行 x {len(header)} 列")
    
    # 保存表格数据
    if all_tables:
        # 合并所有表格
        combined_df = pd.concat(all_tables, ignore_index=True)
        
        # 保存为 Excel 和 CSV
        tables_excel = os.path.join(output_dir, "Akcay_tables.xlsx")
        tables_csv = os.path.join(output_dir, "Akcay_tables.csv")
        
        combined_df.to_excel(tables_excel, index=False)
        combined_df.to_csv(tables_csv, index=False, encoding='utf-8-sig')
        
        print(f"\n表格数据已保存到：")
        print(f"  - Akcay_tables.xlsx")
        print(f"  - Akcay_tables.csv")
        print(f"  共提取 {len(all_tables)} 个表格，总计 {len(combined_df)} 行数据")
    else:
        print("\n未检测到表格数据")
    
    # ========== 提取文本内容 ==========
    print("\n=== 提取文本内容 ===")
    full_text = []
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            full_text.append(f"--- Page {i+1} ---\n{text}")
            print(f"  页面 {i+1}: 提取 {len(text)} 个字符")
    
    # 保存文本内容
    if full_text:
        text_content = "\n\n".join(full_text)
        text_file = os.path.join(output_dir, "Akcay_full_text.txt")
        
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f"\n文本内容已保存到：Akcay_full_text.txt")
        print(f"  总字符数：{len(text_content)}")
        
        return text_content
    else:
        print("\n未提取到文本内容")
        return ""
