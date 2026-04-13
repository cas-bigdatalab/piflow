import shutil
import zipfile

import requests
import os
import sys

"""
    调用远程算子仓库下载接口,将算子文件保存到指定路径

    Args:
        name: 算子名称(对应接口的name参数)
        version: 算子版本(对应接口的version参数)
        output_path: 文件保存路径(包含文件名,如 /tmp/random-selector.zip)

    Raises:
        Exception: 下载过程中出现的各类异常
"""
def download_skill_from_api(name: str, version: str, output_path: str) -> None:

    # 接口基础配置
    BASE_URL = "http://10.0.89.39:8090/api/operators/downloadSkillStream"

    # 构建请求参数
    params = {
        "name": name,
        "version": version
    }

    # 默认请求头
    headers = {
        "Content-Type": "application/json"
    }

    # 定义临时文件句柄,确保全程可关闭
    response = None
    file_handle = None

    try:
        # 预处理路径:Windows下替换反斜杠为正斜杠,避免转义问题
        output_path = output_path.replace("\\", "/")

        # 校验输出路径是否为目录(如果是,自动拼接默认文件名)
        if os.path.isdir(output_path):
            default_filename = f"{name}.zip"
            output_path = os.path.join(output_path, default_filename).replace("\\", "/")
            print(f"检测到输入的是目录,自动拼接文件名:{output_path}")

        # 检查保存目录是否存在,不存在则创建(处理权限)
        save_dir = os.path.dirname(output_path)
        if save_dir and not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir, exist_ok=True)
                print(f"创建保存目录成功:{save_dir}")
            except PermissionError:
                # 权限不足时,提示用户换路径(如桌面)
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                raise Exception(
                    f"创建目录失败:无权限写入 {save_dir}!\n"
                    f"建议更换为桌面路径:{desktop_path}/{name}-{version}.zip"
                )

        # 发送GET请求(流式下载,避免大文件占用过多内存)
        print(f"开始调用接口: {BASE_URL}?name={name}&version={version}")
        with requests.get(
                url=BASE_URL,
                params=params,
                headers=headers,
                stream=True,  # 关键:流式下载
                timeout=300  # 超时时间5分钟,可根据文件大小调整
        ) as response:
            # 检查响应状态码
            response.raise_for_status()

            # 流式写入文件(添加权限异常捕获)
            try:
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):  # 8KB分块
                        if chunk:
                            f.write(chunk)
                # 强制刷新缓冲区并关闭响应流
                response.close()
                del response  # 释放响应对象
            except PermissionError:
                # 权限不足时,提示用户以管理员运行或换路径
                raise Exception(
                    f"写入文件失败:无权限访问 {output_path}!\n"
                    f"解决方案:\n"
                    f"1. 以管理员身份运行Python脚本\n"
                    f"2. 更换保存路径(如桌面:{os.path.join(os.path.expanduser('~'), 'Desktop')})"
                )

            # 验证文件是否保存成功
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = round(os.path.getsize(output_path) / 1024 / 1024, 2)  # 转换为MB
                print(f"\n文件下载成功!")
                print(f"保存路径: {output_path}")
                print(f"文件大小: {file_size} MB")
                # 开始解压保存的zip文件(如果是zip文件)
                # 解压zip文件(核心修复:确保文件未被占用)
                if output_path.lower().endswith(".zip"):
                    try:
                        # 方式1:使用shutil.copyfileobj读取,避免直接占用原文件(备选方案)
                        # 方式2:直接解压,解压完成后强制释放资源
                        extract_dir = os.path.splitext(output_path)[0]
                        # 先删除已存在的解压目录(避免冲突)
                        if os.path.exists(extract_dir):
                            shutil.rmtree(extract_dir)
                        # 解压文件(with语句自动关闭zip文件句柄)
                        with zipfile.ZipFile(output_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_dir)
                        print(f"文件解压成功!解压路径: {extract_dir}")
                        
                        # 检查并处理目录嵌套问题
                        extracted_files = os.listdir(extract_dir)
                        if len(extracted_files) == 1 and os.path.isdir(os.path.join(extract_dir, extracted_files[0])):
                            # 存在嵌套目录，将内容移动到上层目录
                            nested_dir = os.path.join(extract_dir, extracted_files[0])
                            for item in os.listdir(nested_dir):
                                src_path = os.path.join(nested_dir, item)
                                dest_path = os.path.join(extract_dir, item)
                                # 如果目标文件已存在，先删除
                                if os.path.exists(dest_path):
                                    if os.path.isdir(dest_path):
                                        shutil.rmtree(dest_path)
                                    else:
                                        os.remove(dest_path)
                                # 移动文件/目录
                                shutil.move(src_path, extract_dir)
                            # 删除空的嵌套目录
                            shutil.rmtree(nested_dir)
                            print(f"处理目录嵌套成功!移除了多余的嵌套目录: {nested_dir}")

                        # 关键:强制释放文件句柄(Windows特有)
                        import gc
                        gc.collect()  # 触发垃圾回收,释放未关闭的句柄

                        # 删除zip文件(增加重试机制,应对系统延迟释放)
                        max_retry = 3
                        retry_count = 0
                        while retry_count < max_retry:
                            try:
                                os.remove(output_path)
                                print(f"原zip文件已删除:{output_path}")
                                break
                            except PermissionError:
                                retry_count += 1
                                import time
                                time.sleep(0.5)  # 等待0.5秒重试
                                if retry_count == max_retry:
                                    raise Exception(
                                        f"[错误] 重试{max_retry}次仍无法删除文件:{output_path}(文件可能被其他进程占用)")
                    except zipfile.BadZipFile:
                        print("警告: 文件不是有效的zip格式,无法解压")
                    except Exception as e:
                        print(f"警告: 解压/删除文件失败:{str(e)}")
            else:
                raise Exception("文件保存失败,文件为空或未创建")

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            raise Exception(f"接口返回404:算子不存在或Nexus地址为空(name={name}, version={version})")
        elif response.status_code == 500:
            raise Exception(f"接口返回500:服务器内部错误(可能是Nexus下载失败)")
        else:
            raise Exception(f"HTTP请求错误: {e} (状态码: {response.status_code})")
    except requests.exceptions.ConnectionError:
        raise Exception("连接失败:无法访问目标服务器,请检查地址和端口是否正确")
    except requests.exceptions.Timeout:
        raise Exception("请求超时:文件下载时间过长,请检查网络或文件大小")
    except Exception as e:
        raise Exception(f"下载失败: {str(e)}")

def main():
    """脚本主入口:解析命令行参数并执行下载"""
    # 校验命令行参数数量
    if len(sys.argv) != 4:
        print("="*50)
        print("使用方式错误!正确格式:")
        print(f"python {sys.argv[0]} <算子名称> <版本号> <保存路径>")
        print("="*50)
        print("示例:")
        print(f"python {sys.argv[0]} random-selector 0.0.5 D:\\hqr\\workspace\\Agent\\myScripts")
        print(f"python {sys.argv[0]} random-selector 0.0.5 D:\\hqr\\workspace\\Agent\\myScripts\\test.zip")
        sys.exit(1)

    # 解析命令行参数(sys.argv[0]是脚本名,sys.argv[1-3]是传入的参数)
    name = sys.argv[1].strip()
    version = sys.argv[2].strip()
    output_path = sys.argv[3].strip()

    # 校验参数非空
    if not name:
        print("[错误] 算子名称不能为空!")
        sys.exit(1)
    if not version:
        print("[错误] 算子版本不能为空!")
        sys.exit(1)
    if not output_path:
        print("[错误] 保存路径不能为空!")
        sys.exit(1)

    # 执行下载
    try:
        download_skill_from_api(name, version, output_path)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    main()