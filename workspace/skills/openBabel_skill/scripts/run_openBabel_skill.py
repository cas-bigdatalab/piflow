#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import json
import zipfile
import glob
from pathlib import Path


def run_command(cmd_list, stdout_file, stderr_file):
    with open(stdout_file, 'w', encoding='utf-8') as stdout_f, \
         open(stderr_file, 'w', encoding='utf-8') as stderr_f:
        try:
            result = subprocess.run(
                cmd_list,
                stdout=stdout_f,
                stderr=stderr_f,
                check=True,
                text=True
            )
            return True, result.returncode
        except subprocess.CalledProcessError as e:
            return False, e.returncode
        except FileNotFoundError as e:
            with open(stderr_file, 'a', encoding='utf-8') as f:
                f.write(f"Error: {e}\n")
            return False, -1


def convert_with_pybel(input_path, output_path, out_type, is_gen3d, log_path):
    try:
        import pybel
        mol = next(pybel.readfile(input_path.suffix[1:], str(input_path)))
        
        if is_gen3d:
            mol.make3D(forcefield='mmff94', steps=500)
        
        output_format = out_type
        writer = pybel.Outputfile(output_format, str(output_path), overwrite=True)
        writer.write(mol)
        writer.close()
        
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write("Success: converted with pybel\n")
        
        return True
    except ImportError:
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write("Error: pybel module not available\n")
        return False
    except Exception as e:
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write(f"Error: {e}\n")
        return False


def generate_markdown_summary(summary_data, md_file_path):
    lines = [
        "# OpenBabel 格式转换任务摘要",
        "",
        "## 任务状态",
        f"- 状态: {summary_data['status']}",
        f"- 输出目录: {summary_data['outputDir']}",
        "",
        "## 生成文件列表",
        "| 文件路径 | 类型 | 大小 |",
        "|----------|------|------|"
    ]
    for file_info in summary_data.get('generatedFiles', []):
        lines.append(f"| {file_info['path']} | {file_info['type']} | {file_info['size']} |")
    
    lines.extend([
        "",
        "## 结构化摘要",
        f"- 输入文件: {summary_data.get('summary', {}).get('inputFile', '')}",
        f"- 输出格式: {summary_data.get('summary', {}).get('outputType', '')}",
        f"- 生成3D: {summary_data.get('summary', {}).get('gen3d', '')}",
        f"- 输出文件: {summary_data.get('summary', {}).get('outputFile', '')}",
        "",
        "## 日志路径",
        f"- 主日志: {summary_data.get('rawLogPath', '')}",
        f"- stdout: {summary_data.get('stdoutPath', '')}",
        f"- stderr: {summary_data.get('stderrPath', '')}"
    ])
    
    if summary_data.get('errorMessage'):
        lines.extend([
            "",
            "## 错误信息",
            summary_data['errorMessage']
        ])
    
    with open(md_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='分子格式转换工具，支持多种格式之间的转换和3D构象生成')
    parser.add_argument('--inputPath', required=True, help='输入文件完整路径')
    parser.add_argument('--outType', required=True, help='输出格式，如xyz、mol、gjf、sdf')
    parser.add_argument('--isGen3d', required=True, type=bool, help='是否生成3D构象')
    parser.add_argument('--outputDir', required=True, help='本次任务输出的工作目录')
    parser.add_argument('--primaryOutputPath', required=True, help='主输出文件完整路径')
    parser.add_argument('--compressedOutputPath', required=True, help='其他输出文件压缩包完整路径')
    
    args = parser.parse_args()
    
    input_path = Path(args.inputPath)
    output_dir = Path(args.outputDir)
    primary_output_path = Path(args.primaryOutputPath)
    compressed_output_path = Path(args.compressedOutputPath)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    primary_output_path.parent.mkdir(parents=True, exist_ok=True)
    compressed_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        error_output = {
            "status": "failed",
            "outputDir": str(output_dir),
            "primaryOutputPath": "",
            "compressedOutputPath": "",
            "errorMessage": f"输入文件不存在: {input_path}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    expected_ext = args.outType
    actual_ext = primary_output_path.suffix[1:] if primary_output_path.suffix else ''
    
    if actual_ext.lower() != expected_ext.lower():
        error_output = {
            "status": "failed",
            "outputDir": str(output_dir),
            "primaryOutputPath": "",
            "compressedOutputPath": "",
            "errorMessage": f"primaryOutputPath 的扩展名({actual_ext})与 outType({expected_ext})不一致"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    log_path = output_dir / "openbabel.log"
    
    other_param = "--gen3d -best" if args.isGen3d else ""
    
    obabel_cmds = [
        ["obabel", str(input_path), "-O", str(primary_output_path)] + (other_param.split() if other_param else []),
        ["openbabel.obabel", str(input_path), "-O", str(primary_output_path)] + (other_param.split() if other_param else [])
    ]
    
    success = False
    last_error = ""
    
    for cmd in obabel_cmds:
        cmd_str = ' '.join(cmd)
        print(f"Trying command: {cmd_str}")
        
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write(f"Command: {cmd_str}\n")
        
        success, return_code = run_command(cmd, str(stdout_path), str(stderr_path))
        
        if success and primary_output_path.exists():
            print(f"Command succeeded with return code: {return_code}")
            with open(log_path, 'a', encoding='utf-8') as log_f:
                log_f.write(f"Success, return code: {return_code}\n")
            break
        else:
            with open(log_path, 'a', encoding='utf-8') as log_f:
                log_f.write(f"Failed, return code: {return_code}\n")
            last_error = f"Command failed: {cmd_str}"
    
    if not success or not primary_output_path.exists():
        print("Trying pybel module...")
        with open(log_path, 'a', encoding='utf-8') as log_f:
            log_f.write("Trying pybel module...\n")
        
        if convert_with_pybel(input_path, primary_output_path, args.outType, args.isGen3d, log_path):
            success = True
            print("Success: converted with pybel")
        else:
            last_error = "所有尝试的转换方式都失败了，请确保已安装openbabel"
    
    if not success or not primary_output_path.exists():
        error_output = {
            "status": "failed",
            "outputDir": str(output_dir),
            "primaryOutputPath": "",
            "compressedOutputPath": "",
            "errorMessage": last_error or "所有尝试的转换方式都失败了"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    generated_files = []
    
    if primary_output_path.exists():
        file_size = primary_output_path.stat().st_size
        generated_files.append({
            "path": str(primary_output_path),
            "type": "主输出文件",
            "size": file_size
        })
    
    for ext in ['log', 'txt']:
        for f in output_dir.glob(f'*.{ext}'):
            if f != primary_output_path:
                file_size = f.stat().st_size
                generated_files.append({
                    "path": str(f),
                    "type": "日志文件" if ext == 'log' else "文本文件",
                    "size": file_size
                })
    
    summary_data = {
        "status": "success",
        "outputDir": str(output_dir),
        "generatedFiles": generated_files,
        "summary": {
            "inputFile": str(input_path),
            "outputType": args.outType,
            "gen3d": args.isGen3d,
            "outputFile": str(primary_output_path)
        },
        "rawLogPath": str(log_path),
        "stdoutPath": str(stdout_path),
        "stderrPath": str(stderr_path),
        "errorMessage": ""
    }
    
    md_summary_path = output_dir / "summary.md"
    generate_markdown_summary(summary_data, md_summary_path)
    
    generated_files.append({
        "path": str(md_summary_path),
        "type": "摘要文件",
        "size": md_summary_path.stat().st_size
    })
    
    with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in generated_files:
            file_path = Path(f["path"])
            if file_path.exists():
                zf.write(file_path, file_path.name)
    
    final_output = {
        "status": "success",
        "outputDir": str(output_dir),
        "primaryOutputPath": str(primary_output_path),
        "compressedOutputPath": str(compressed_output_path)
    }
    
    print(json.dumps(final_output, ensure_ascii=False))


if __name__ == "__main__":
    main()