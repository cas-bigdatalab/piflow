#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bdbe_scnorm: 单细胞测序数据标准化处理
"""

import argparse
import requests
import json
import time
import os
from urllib.parse import quote


def upload_file(input_file, tool='scPrep'):
    """
    上传文件到服务器
    
    :param input_file: 输入文件路径
    :param tool: 工具名称，固定为scPrep
    :return: 文件ID
    """
    url = "https://www.bdbe.cn/kun/api/upload"
    
    try:
        # 检查文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 文件不存在: {input_file}")
            return None
        
        # 检查文件大小
        file_size = os.path.getsize(input_file)
        print(f"文件大小: {file_size / 1024:.2f} KB")
        
        # 构建请求数据，与Postman一致
        files = {
            'ds': (os.path.basename(input_file), open(input_file, 'rb'), 'text/csv')
        }
        data = {
            'tool': tool
        }
        
        print(f"正在上传文件: {input_file}")
        print(f"上传URL: {url}")
        print(f"工具: {tool}")
        print(f"文件名: {os.path.basename(input_file)}")
        
        # 不设置Content-Type，让requests自动处理
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.post(url, files=files, data=data, headers=headers, timeout=120)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        response.raise_for_status()
        result = response.json()
        
        print(f"响应JSON: {result}")
        
        if result.get('code') != 0:
            error_msg = result.get('msg', result.get('message', '未知错误'))
            print(f"上传失败: {error_msg}")
            print("可能的原因：")
            print("1. 文件格式不支持 - 服务器可能只接受特定格式文件")
            print("2. 文件大小超过限制 - 当前文件大小: {:.2f} KB".format(file_size / 1024))
            print("3. 文件内容不符合要求")
            return None
        
        file_id = result.get('id')
        print(f"上传成功，文件ID: {file_id}")
        return file_id
        
    except FileNotFoundError:
        print(f"错误: 文件不存在: {input_file}")
        return None
    except requests.RequestException as e:
        print(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("错误: 无法解析响应结果")
        return None


def start_analysis(file_id, species, tool='scPrep'):
    """
    启动标准化分析
    
    :param file_id: 上传文件ID
    :param species: 物种类型
    :param tool: 工具名称，固定为scPrep
    :return: 分析任务ID
    """
    url = f"https://www.bdbe.cn/kun/api/analysis?tool={tool}&id={file_id}&species={species}"
    
    try:
        print("\n正在启动标准化分析...")
        response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') != 0:
            print(f"分析任务启动失败: {result.get('message', '未知错误')}")
            return None
        
        task_id = result.get('id')
        print(f"分析任务启动成功，任务ID: {task_id}")
        return task_id
        
    except requests.RequestException as e:
        print(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("错误: 无法解析响应结果")
        return None


def get_result(task_id, max_retries=30, retry_interval=5):
    """
    获取分析结果
    
    :param task_id: 分析任务ID
    :param max_retries: 最大重试次数
    :param retry_interval: 重试间隔（秒）
    :return: 分析结果
    """
    url = f"https://www.bdbe.cn/kun/api/result?id={task_id}"
    
    for i in range(max_retries):
        try:
            print(f"\n正在获取分析结果... (尝试 {i+1}/{max_retries})")
            response = requests.get(url, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            code = result.get('code')
            if code == 1:
                print("分析完成！")
                return result
            elif code == 0:
                print("分析正在进行中，等待...")
                time.sleep(retry_interval)
            else:
                print(f"分析失败，状态码: {code}")
                return None
                
        except requests.RequestException as e:
            print(f"请求失败: {str(e)}")
            time.sleep(retry_interval)
        except json.JSONDecodeError:
            print("错误: 无法解析响应结果")
            time.sleep(retry_interval)
    
    print("分析超时，未能获取结果")
    return None


def download_file(url, save_path):
    """
    下载文件
    
    :param url: 下载链接
    :param save_path: 保存路径
    :return: 是否下载成功
    """
    try:
        # 确保保存目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        print(f"正在下载文件: {url}")
        print(f"保存路径: {save_path}")
        
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"下载成功: {os.path.basename(save_path)}")
        return True
    except Exception as e:
        print(f"下载失败: {str(e)}")
        return False


def format_result(result, output_dir):
    """
    格式化展示分析结果并下载文件
    
    :param result: 分析结果
    :param output_dir: 输出目录
    """
    if not result:
        print("无分析结果")
        return
    
    code = result.get('code', -1)
    if code != 1:
        print(f"分析失败，状态码: {code}")
        return
    
    content = result.get('content', [])
    main_link = result.get('link', '')
    
    print("分析完成，结果文件：")
    print()
    
    # 提取核心文件和辅助文件
    core_files = []
    auxiliary_files = []
    
    for item in content:
        label = item.get('label', '')
        children = item.get('children', [])
        
        if label == 'mouse':
            core_files.extend(children)
        elif label == 'hf':
            auxiliary_files.extend(children)
    
    # 展示核心文件并下载
    if core_files:
        print("核心文件：")
        for file in core_files:
            file_name = file.get('label', '未知')
            file_link = file.get('link', '')
            full_link = f"https://www.bdbe.cn/kun/api/download?name={quote(file_link)}" if file_link else "无"
            print(f"- {file_name}")
            print(f"  下载链接: {full_link}")
            
            # 下载文件
            if full_link != "无" and output_dir:
                save_path = os.path.join(output_dir, file_name)
                download_file(full_link, save_path)
        print()
    
    # 展示辅助文件
    if auxiliary_files:
        print("辅助文件：")
        for file in auxiliary_files:
            file_name = file.get('label', '未知')
            print(f"- {file_name}")
        print()


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='单细胞测序数据标准化处理')
    parser.add_argument('--input_file', type=str, required=True, help='输入单细胞测序数据文件路径')
    parser.add_argument('--species', type=str, required=True, help='物种类型，如 mouse、human 等')
    parser.add_argument('--output_dir', type=str, help='输出目录，默认在上传文件所在目录')
    
    args = parser.parse_args()
    
    # 确定输出目录
    output_dir = args.output_dir
    if not output_dir:
        output_dir = os.path.dirname(args.input_file)
    print(f"输出目录: {output_dir}")
    
    # 第一步：上传文件
    file_id = upload_file(args.input_file)
    if not file_id:
        return 1
    
    # 第二步：启动分析
    task_id = start_analysis(file_id, args.species)
    if not task_id:
        return 1
    
    # 第三步：获取结果
    result = get_result(task_id)
    if not result:
        return 1
    
    # 格式化展示结果并下载文件
    format_result(result, output_dir)
    
    return 0


if __name__ == "__main__":
    exit(main())
