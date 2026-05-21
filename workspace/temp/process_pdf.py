import pdfplumber
import pandas as pd
import os

pdf_path = "/temp/Akcay.pdf"
output_dir = "/outputs"
artifacts_dir = "/artifacts"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)
os.makedirs(artifacts_dir, exist_ok=True)

# 存储所有提取内容
all_text = []
all_tables = []

# 读取 PDF
with pdfplumber.open(pdf_path) as pdf:
    # 提取文本和表格
    for i, page in enumerate(pdf.pages):
        print(f"处理第 {i+1} 页，共 {len(pdf.pages)} 页")
        
        # 提取文本
        text = page.extract_text()
        if text:
            all_text.append(f"=== 第 {i+1} 页 ===\n{text}")
        
        # 提取表格
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"  - 发现表格 {j+1}")
            if table:
                # 转换为 DataFrame 并保存
                df = pd.DataFrame(table)
                all_tables.append({
                    'page': i + 1,
                    'table_num': j + 1,
                    'data': df
                })

# 保存完整文本
full_text = "\n\n".join(all_text)
text_output_path = os.path.join(artifacts_dir, "extracted_text.txt")
with open(text_output_path, 'w', encoding='utf-8') as f:
    f.write(full_text)
print(f"\n文本已保存到：{text_output_path}")

# 保存表格
for table_info in all_tables:
    table_file = os.path.join(output_dir, f"table_page{table_info['page']}_num{table_info['table_num']}.csv")
    table_info['data'].to_csv(table_file, index=False, header=False, encoding='utf-8-sig')
    print(f"表格已保存到：table_page{table_info['page']}_num{table_info['table_num']}.csv")

# 生成摘要报告
summary_report = f"""# PDF 摘要报告

## 基本信息
- 文件名：Akcay.pdf
- 总页数：{len(pdf.pages)}
- 提取表格数量：{len(all_tables)}

## 文本摘要
"""

# 简单摘要：提取每页前几行
for i, text_page in enumerate(all_text[:5]):  # 限制前 5 页
    lines = text_page.split('\n')[:10]  # 每页前 10 行
    summary_report += f"\n### 第 {i+1} 页摘要\n"
    summary_report += "\n".join(lines) + "\n"

summary_report += f"\n## 表格概览\n"
for table_info in all_tables:
    summary_report += f"\n- 第 {table_info['page']} 页 - 表格 {table_info['table_num']}: {table_info['data'].shape[0]} 行 × {table_info['data'].shape[1]} 列\n"

summary_output_path = os.path.join(output_dir, "摘要报告.md")
with open(summary_output_path, 'w', encoding='utf-8') as f:
    f.write(summary_report)

print(f"\n摘要报告已保存到：摘要报告.md")
print(f"\n处理完成！共提取 {len(all_tables)} 个表格")
