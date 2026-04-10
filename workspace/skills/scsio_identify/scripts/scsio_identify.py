#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scsio_identify: 调用中国科学院南海海洋研究所的海洋生物识别服务
"""

import argparse
import requests
import json


def identify_marine_organism(image_file, threshold=0.1):
    """
    调用海洋生物识别服务
    
    :param image_file: 图片文件路径
    :param threshold: 相似度阈值
    :return: 识别结果
    """
    # API接口地址
    url = "https://data.scsio.ac.cn/api/web/v1/image/identify/animal"
    
    try:
        # 读取图片文件
        with open(image_file, 'rb') as f:
            files = {'file': f}
            
            # 发送请求
            print(f"正在上传图片: {image_file}")
            response = requests.post(url, files=files, timeout=30)
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            # 检查API返回状态
            if result.get('statusCode') != 200:
                print(f"识别失败: {result.get('message', '未知错误')}")
                return None
            
            return result
            
    except FileNotFoundError:
        print(f"错误: 文件不存在: {image_file}")
        return None
    except requests.RequestException as e:
        print(f"请求失败: {str(e)}")
        return None
    except json.JSONDecodeError:
        print("错误: 无法解析响应结果")
        return None


def format_result(result, threshold=0.1):
    """
    格式化展示识别结果
    
    :param result: 识别结果
    :param threshold: 相似度阈值
    """
    if not result or 'data' not in result:
        print("无识别结果")
        return
    
    data = result['data']
    log_id = data.get('log_id', 'N/A')
    identification_results = data.get('result', [])
    
    print("识别结果：")
    
    # 按相似度排序（降序）
    sorted_results = sorted(identification_results, key=lambda x: float(x.get('score', '0')), reverse=True)
    
    # 筛选高于阈值的结果
    filtered_results = [r for r in sorted_results if float(r.get('score', '0')) >= threshold]
    
    if not filtered_results:
        print("无符合阈值的识别结果")
        return
    
    for i, item in enumerate(filtered_results, 1):
        name = item.get('name', '未知')
        score = float(item.get('score', '0'))
        print(f"{i}. {name} - 相似度: {score:.2%}")
    
    print(f"\n日志ID: {log_id}")


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='识别海洋生物')
    parser.add_argument('--image_file', type=str, required=True, help='图片文件路径')
    parser.add_argument('--threshold', type=float, default=0.1, help='相似度阈值')
    
    args = parser.parse_args()
    
    # 验证参数
    if args.threshold < 0 or args.threshold > 1:
        print("错误: 阈值必须在0-1之间")
        return 1
    
    # 调用识别服务
    result = identify_marine_organism(args.image_file, args.threshold)
    
    # 格式化展示结果
    if result:
        format_result(result, args.threshold)
    
    return 0


if __name__ == "__main__":
    exit(main())
