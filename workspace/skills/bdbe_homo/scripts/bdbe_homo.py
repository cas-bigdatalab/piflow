#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bdbe_homo: 检索单细胞测序相关的预训练数据集
"""

import argparse
import requests
import json
import tempfile
import os


def query_single_cell_datasets(organism, organ=None, class_=None, time=None, 
                              gender=None, cell_line=None, organoid=None, 
                              tumor=None, page_num=1, page_size=10):
    """
    调用单细胞预训练数据集检索服务
    
    :param organism: 生物物种
    :param organ: 组织/器官
    :param class_: 分类
    :param time: 发育/采样时间
    :param gender: 性别
    :param cell_line: 细胞系
    :param organoid: 类器官
    :param tumor: 肿瘤相关
    :param page_num: 分页页码
    :param page_size: 每页返回数据集数量
    :return: 检索结果
    """
    # API接口地址
    base_url = "https://www.bdbe.cn/kun/api/homo"
    
    # 构建查询参数
    params = {
        'Organism': organism,
        'Organ': organ or '',
        'Class': class_ or '',
        'Time': time or '',
        'Gender': gender or '',
        'Cell_line': cell_line or '',
        'Organoid': organoid or '',
        'Tumor': tumor or '',
        'pageNum': page_num,
        'pagesize': page_size
    }
    
    try:
        # 发送请求
        print(f"正在查询单细胞预训练数据集...")
        response = requests.get(base_url, params=params, timeout=30)
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析响应
        result = response.json()
        
        # 检查API返回状态
        if result.get('code') != 0:
            print(f"查询失败: {result.get('message', '未知错误')}")
            return None
        
        return result
        
    except requests.RequestException as e:
        print(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("错误: 无法解析响应结果")
        return None


def format_result(result):
    """
    格式化展示查询结果
    
    :param result: 检索结果
    """
    if not result:
        print("无查询结果")
        return
    
    code = result.get('code', -1)
    if code != 0:
        print(f"查询失败，状态码: {code}")
        return
    
    content = result.get('content', [])
    total = result.get('total', 0)
    
    print(f"查询结果：")
    print(f"总数据集数量: {total}")
    print()
    
    if not content:
        print("无符合条件的数据集")
        return
    
    # 检查结果长度，决定是否输出到临时文件
    result_str = f"查询结果：\n总数据集数量: {total}\n\n"
    
    for i, item in enumerate(content, 1):
        result_str += f"数据集 {i}:\n"
        result_str += f"- ID: {item.get('id', 'N/A')}\n"
        result_str += f"- 唯一标识: {item.get('sid', 'N/A')}\n"
        result_str += f"- 样本编号: {item.get('sample', 'N/A')}\n"
        result_str += f"- 生物物种: {item.get('organism', 'N/A')}\n"
        result_str += f"- 分类: {item.get('class', 'N/A')}\n"
        result_str += f"- 组织/器官: {item.get('organ', 'N/A')}\n"
        result_str += f"- 细胞系: {item.get('cell_line', 'N/A')}\n"
        result_str += f"- 发育/采样时间: {item.get('time', 'N/A')}\n"
        result_str += f"- 性别: {item.get('gender', 'N/A')}\n"
        result_str += f"- 系列编号: {item.get('series', 'N/A')}\n"
        result_str += f"- 原始数据量: {item.get('num_raw', 'N/A')}\n"
        result_str += f"- 质控后数据量: {item.get('num_qc', 'N/A')}\n"
        result_str += f"- 注释后数据量: {item.get('num_annotation', 'N/A')}\n"
        result_str += f"- 数据文件路径: {item.get('detail', 'N/A')}\n"
        result_str += f"- 数据授权类型: {item.get('license', 'N/A')}\n"
        result_str += f"- 测序平台: {item.get('system', 'N/A')}\n\n"
    
    # 如果结果过长，输出到临时文件
    if len(result_str) > 5000:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(result_str)
            temp_file = f.name
        
        print(f"结果过长，已输出到临时文件: {temp_file}")
        print("文件内容：")
        print("=" * 80)
        with open(temp_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("=" * 80)
        
        # 删除临时文件
        try:
            os.unlink(temp_file)
            print(f"临时文件已删除: {temp_file}")
        except:
            pass
    else:
        print(result_str)


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='检索单细胞测序相关的预训练数据集')
    parser.add_argument('--organism', type=str, required=True, help='生物物种（必填）')
    parser.add_argument('--organ', type=str, default=None, help='组织/器官')
    parser.add_argument('--class', dest='class_', type=str, default=None, help='分类')
    parser.add_argument('--time', type=str, default=None, help='发育/采样时间')
    parser.add_argument('--gender', type=str, default=None, help='性别')
    parser.add_argument('--cell_line', type=str, default=None, help='细胞系')
    parser.add_argument('--organoid', type=str, default=None, help='类器官')
    parser.add_argument('--tumor', type=str, default=None, help='肿瘤相关')
    parser.add_argument('--page_num', type=int, default=1, help='分页页码（从1开始）')
    parser.add_argument('--page_size', type=int, default=10, help='每页返回数据集数量')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.page_num < 1:
        print("错误: 页码必须大于等于1")
        return 1
    
    if args.page_size < 1:
        print("错误: 每页数量必须大于等于1")
        return 1
    
    # 调用查询服务
    result = query_single_cell_datasets(
        args.organism,
        args.organ,
        args.class_,
        args.time,
        args.gender,
        args.cell_line,
        args.organoid,
        args.tumor,
        args.page_num,
        args.page_size
    )
    
    # 格式化展示结果
    if result:
        format_result(result)
    
    return 0


if __name__ == "__main__":
    exit(main())
