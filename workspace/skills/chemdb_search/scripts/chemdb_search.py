#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化学物质基础数据库搜索脚本

该脚本用于调用化学物质基础数据库搜索服务，根据输入的化学分子式检索并返回对应的化学物质详细信息。
"""

import argparse
import json
import requests
import sys


def check_python_version():
    """
    检查Python版本是否满足要求
    
    Returns:
        bool: 是否满足Python 3.9+版本要求
    """
    required_version = (3, 9)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"错误: Python版本过低。当前版本: {current_version.major}.{current_version.minor}.{current_version.micro}")
        print(f"请安装Python {required_version[0]}.{required_version[1]} 或更高版本。")
        return False
    return True


def search_chemdb(text, page=1, page_size=10):
    """
    调用化学物质基础数据库搜索服务
    
    Args:
        text (str): 化学分子式
        page (int): 分页页码
        page_size (int): 每页返回数量
        
    Returns:
        dict: 搜索结果
    """
    url = "http://www.chemdb.csdb.cn/chemdb_backend/search/text_search"
    params = {
        "text": text,
        "page": page,
        "page_size": page_size
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # 检查HTTP响应状态
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "code": 500,
            "message": f"网络请求失败: {str(e)}",
            "data": [],
            "page_all": 0,
            "total": 0
        }
    except json.JSONDecodeError as e:
        return {
            "code": 500,
            "message": f"JSON解析失败: {str(e)}",
            "data": [],
            "page_all": 0,
            "total": 0
        }


def main():
    """
    主函数
    """
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="化学物质基础数据库搜索工具")
    parser.add_argument("--text", required=True, help="化学分子式（如 C6H6、C12H12）")
    parser.add_argument("--page", type=int, default=1, help="分页页码（从 1 开始）")
    parser.add_argument("--page_size", type=int, default=10, help="每页返回的化学物质数量")
    
    args = parser.parse_args()
    
    # 调用搜索函数
    result = search_chemdb(args.text, args.page, args.page_size)
    
    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
