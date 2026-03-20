#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取算子仓库中skill的基本信息
调用算子仓库listAllSkills接口，获取并格式化输出所有算子信息（名称、版本号、功能描述）
"""
import requests
import json
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import argparse

def list_all_skills(page_num=None, page_size=None) -> None:
    # 接口配置
    API_URL = "http://10.0.89.39:8090/api/operators/listAllSkills"
    TIMEOUT = 10  # 请求超时时间(秒)

    try:
        # 构建请求参数
        params = {}
        if page_num is not None:
            params['pageNum'] = page_num
        if page_size is not None:
            params['pageSize'] = page_size

        # 发送GET请求
        print(f"[开始] 调用算子列表接口:{API_URL}")
        if params:
            print(f"[参数] pageNum={page_num}, pageSize={page_size}")
        response = requests.get(
            url=API_URL,
            params=params,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )

        # 校验响应状态
        response.raise_for_status()

        # 确保响应内容使用UTF-8解码
        response.encoding = 'utf-8'
        skill_data = response.json()

        # 格式化输出
        print("\n" + "=" * 80)
        print("当前算子仓库算子列表")
        print("=" * 80)

        # 处理返回数据
        total = 0
        current_page_size = 0
        skill_list = []

        if isinstance(skill_data, dict):
            # 新的返回结构: {"code": 200, "data": {"total": 35, "currentPageSize": 35, "skillOpsList": [...]}, "errorMsg": "成功"}
            if skill_data.get("code") == 200:
                data = skill_data.get("data", {})
                total = data.get("total", 0)
                current_page_size = data.get("currentPageSize", 0)
                skill_list = data.get("skillOpsList", [])
            else:
                # 兼容旧格式: 直接是包含列表的字典
                skill_list = skill_data.get("data", skill_data.get("skills", skill_data.get("list", [])))
        elif isinstance(skill_data, list):
            # 兼容旧格式: 返回直接是算子列表
            skill_list = skill_data

        # 输出技能信息
        if len(skill_list) == 0:
            print("⚠️  算子仓库暂无算子数据")
        else:
            for idx, skill in enumerate(skill_list, 1):
                # 提取核心字段
                name = skill.get("name", "未知名称")
                version = skill.get("version", "未知版本")
                description = skill.get("description", "无描述")
                nexus_url = skill.get("nexusUrl", "无Nexus地址")

                print(f"\n{idx}. 算子名称:{name}")
                print(f"   版本号:{version}")
                print(f"   功能描述:{description}")
                print(f"   Nexus地址:{nexus_url}")

        print("\n" + "=" * 80)
        if total > 0:
            print(f"算子列表获取完成,总计 {total} 个算子")
            if current_page_size > 0:
                print(f"当前页显示 {current_page_size} 个算子")
        else:
            print(f"算子列表获取完成,共查询到 {len(skill_list)} 个算子")

    except requests.exceptions.ConnectionError:
        print(f"连接失败:无法访问算子仓库服务({API_URL}),请检查服务是否启动或网络是否通畅")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"请求超时:接口响应超过 {TIMEOUT} 秒,请检查服务响应速度")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"接口请求失败:HTTP状态码 {e.response.status_code}")
        if e.response.status_code == 404:
            print("   可能原因:接口路径错误,请核对listAllSkills接口地址")
        elif e.response.status_code == 500:
            print("   可能原因:算子仓库服务内部错误,请联系服务维护人员")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"数据解析失败:接口返回非JSON格式数据,原始响应:\n{response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"未知错误:{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='获取算子仓库中skill的基本信息')
    parser.add_argument('--page_num', type=int, default=None, help='页码（可选）')
    parser.add_argument('--page_size', type=int, default=None, help='每页大小（可选）')
    args = parser.parse_args()
    list_all_skills(page_num=args.page_num, page_size=args.page_size)