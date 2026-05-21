import pdfplumber
import csv
import json

pdf_path = "/temp/Akcay.pdf"
tables_output = "/artifacts/tables_data.json"
text_output = "/artifacts/full_text.txt"

all_tables = []
full_text = ""

with pdfplumber.open(pdf_path) as pdf:
    print(f"PDF 总页数：{len(pdf.pages)}")
    
    # 提取表格和文本
    for i, page in enumerate(pdf.pages):
        print(f"处理第 {i+1} 页...")
        
        # 提取文本
        page_text = page.extract_text()
        if page_text:
            full_text += f"--- 第 {i+1} 页 ---\n"
            full_text += page_text + "\n\n"
        
        # 提取表格
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            if table:
                table_data = {
                    "page": i + 1,
                    "table_index": j + 1,
                    "rows": table
                }
                all_tables.append(table_data)
                print(f"  - 发现表格 {j+1}，行数：{len(table)}")

# 保存表格数据为 JSON
with open(tables_output, 'w', encoding='utf-8') as f:
    json.dump(all_tables, f, ensure_ascii=False, indent=2)

print(f"\n表格数据已保存到：{tables_output}")
print(f"共提取 {len(all_tables)} 个表格")

# 保存全文文本
with open(text_output, 'w', encoding='utf-8') as f:
    f.write(full_text)

print(f"文本内容已保存到：{text_output}")
print(f"文本总长度：{len(full_text)} 字符")
