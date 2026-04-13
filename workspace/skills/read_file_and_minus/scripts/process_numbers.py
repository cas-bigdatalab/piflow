#!/usr/bin/env python3
"""
Minus numbers by 5 processing script
Read numbers from text file, minus each by 5, save to output file
"""

import re
import sys
import os


def read_file_and_minus(filename, separator=None):
    """
    读取文本文件，按分隔符分割内容，并将每个数字减去5

    Args:
        filename (str): 要读取的文件名
        separator (str, optional): 自定义分隔符，默认为 None（使用多种分隔符）

    Returns:
        list: 处理后的数字列表
    """
    try:
        # 读取文件内容
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read().strip()

        # 如果没有指定分隔符，使用多种分隔符进行分割
        if separator is None:
            # 使用正则表达式匹配多种分隔符：空格、换行、顿号、逗号等
            parts = re.split(r'[\s、,\，]+', content)
        else:
            parts = content.split(separator)

        # 过滤掉空字符串并转换为数字
        numbers = []
        for part in parts:
            part = part.strip()
            if part:  # 确保不是空字符串
                try:
                    num = float(part)  # 支持整数和小数
                    numbers.append(num -5)  # 每个数字减去5
                except ValueError:
                    print(f"警告: '{part}' 不是有效数字，已跳过")

        return numbers

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{filename}'")
        return []
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return []


def save_result_to_file(numbers, output_filename):
    """
    将结果保存到文件

    Args:
        numbers (list): 数字列表
        output_filename (str): 输出文件名
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(output_filename, 'w', encoding='utf-8') as file:
            for num in numbers:
                # 如果是整数则显示为整数，否则保留小数
                if num.is_integer():
                    file.write(f"{int(num)}\n")
                else:
                    file.write(f"{num}\n")
        print(f"结果已保存到 '{output_filename}'")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False


def get_user_input():
    """获取用户输入的文件路径"""
    print("=== 文件数字处理工具 ===")
    print("功能：读取文件中的数字，每个数字减去5后保存")
    print()

    # 获取输入文件路径
    while True:
        input_file = input("请输入要处理的文件路径: ").strip()
        if not input_file:
            print("文件路径不能为空，请重新输入")
            continue

        # 检查文件是否存在
        if os.path.exists(input_file):
            break
        else:
            print(f"文件 '{input_file}' 不存在，请检查路径是否正确")

    # 获取输出文件路径
    default_output = f"{os.path.splitext(input_file)[0]}_result.txt"
    output_file = input(f"请输入输出文件路径 (直接回车使用默认路径 '{default_output}'): ").strip()

    if not output_file:
        output_file = default_output

    # 确认处理选项
    print(f"\n确认信息:")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")

    return input_file, output_file

def process():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) >= 3 else f"{os.path.splitext(input_file)[0]}_result.txt"

        # 验证输入文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 输入文件 '{input_file}' 不存在")
            return
    else:
        # 交互式获取用户输入
        input_file, output_file = get_user_input()
        if not input_file:
            return

    print(f"\n正在处理文件: {input_file}")

    # 处理文件
    result = read_file_and_minus(input_file)

    if result:
        print(f"找到 {len(result)} 个数字")
        print("处理结果:", result)

        # 保存结果
        if save_result_to_file(result, output_file):
            print("处理完成！")
        else:
            print("处理失败！")
    else:
        print("未找到有效的数字数据")

# 示例用法
if __name__ == "__main__":
    process()


