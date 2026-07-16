#!/usr/bin/env python3
"""
Convert Gaussian chk file to fchk using formchk.
Compatible with both Windows and Linux.
"""

import argparse
import os
import subprocess
import sys
import zipfile
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Convert Gaussian chk file to fchk')
    parser.add_argument('--input_path', required=True, help='Input chk file path')
    parser.add_argument('--other_param', help='Additional parameters')
    parser.add_argument('--fchk_output_path', required=True, help='Output fchk file path')
    parser.add_argument('--compressed_output_path', required=True, help='Output zip file path')
    args = parser.parse_args()

    input_path = Path(args.input_path)
    fchk_output_path = Path(args.fchk_output_path)
    compressed_output_path = Path(args.compressed_output_path)
    
    output_dir = fchk_output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stderr_content = ""
    stderr_log_path = output_dir / 'stderr.log'

    if not input_path.exists():
        error_output = {
            "status": "failed",
            "fchk_output_path": "",
            "compressed_output_path": "",
            "errorMessage": f"Input file not found: {args.input_path}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)

    is_windows = sys.platform.startswith('win')
    
    formchk_path = None
    env = os.environ.copy()

    if is_windows:
        g16_path_str = os.environ.get('g16root', '')
        if g16_path_str:
            g16_path = Path(g16_path_str)
            if not g16_path.is_file():
                g16_path = g16_path / 'g16.exe'
            if g16_path.exists():
                formchk_path = g16_path.parent / 'formchk.exe'
        
        if not formchk_path or not formchk_path.exists():
            search_paths = [
                Path('C:/G16W/formchk.exe'),
                Path('C:/Gaussian/g16/formchk.exe'),
                Path('C:/Program Files/Gaussian/g16/formchk.exe')
            ]
            for p in search_paths:
                if p.exists():
                    formchk_path = p
                    break
        
        if not formchk_path or not formchk_path.exists():
            error_output = {
                "status": "failed",
                "fchk_output_path": "",
                "compressed_output_path": "",
                "errorMessage": "formchk not found. Please set g16root environment variable or install Gaussian."
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
    else:
        g16root = None
        gauss_exedir = None
        
        try:
            result = subprocess.run(
                ['bash', '--norc', '-c', 'set +e; source ~/.bashrc 2>/dev/null; echo "g16root=${g16root:-}"; echo "GAUSS_EXEDIR=${GAUSS_EXEDIR:-}"'],
                capture_output=True,
                text=True,
                check=True
            )
            for line in result.stdout.split('\n'):
                if line.startswith('g16root='):
                    g16root = line.split('=', 1)[1]
                elif line.startswith('GAUSS_EXEDIR='):
                    gauss_exedir = line.split('=', 1)[1]
        except Exception:
            pass
        
        if not g16root:
            g16root = '$HOME/gaussian'
        if not gauss_exedir:
            gauss_exedir = f'{g16root}/g16'
        
        formchk_path = Path(f"{gauss_exedir}/formchk")
        
        if not formchk_path.exists():
            error_output = {
                "status": "failed",
                "fchk_output_path": "",
                "compressed_output_path": "",
                "errorMessage": f"formchk not found at {formchk_path}"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)

    formchk_cmd = [str(formchk_path), str(input_path), str(fchk_output_path)]
    print(f"$$command: {' '.join(formchk_cmd)}")

    try:
        result = subprocess.run(
            formchk_cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
            stderr_content += "formchk STDERR:\n" + result.stderr + "\n"
    except subprocess.CalledProcessError as e:
        stderr_content += f"Error executing formchk: {e}\n"
        if e.stdout:
            stderr_content += f"STDOUT: {e.stdout}\n"
        if e.stderr:
            stderr_content += f"STDERR: {e.stderr}\n"
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)
        
        with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if stderr_log_path.exists():
                zf.write(stderr_log_path, stderr_log_path.name)
        
        error_output = {
            "status": "failed",
            "fchk_output_path": "",
            "compressed_output_path": str(compressed_output_path),
            "errorMessage": f"Error executing formchk: {e}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        stderr_content += f"Unexpected error: {e}\n"
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)
        
        with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if stderr_log_path.exists():
                zf.write(stderr_log_path, stderr_log_path.name)
        
        error_output = {
            "status": "failed",
            "fchk_output_path": "",
            "compressed_output_path": str(compressed_output_path),
            "errorMessage": f"Unexpected error: {e}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)

    if stderr_content:
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)

    with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if fchk_output_path.exists():
            zf.write(fchk_output_path, fchk_output_path.name)
        if stderr_log_path.exists():
            zf.write(stderr_log_path, stderr_log_path.name)

    success_output = {
        "status": "success",
        "fchk_output_path": str(fchk_output_path),
        "compressed_output_path": str(compressed_output_path)
    }
    print(json.dumps(success_output, ensure_ascii=False))


if __name__ == '__main__':
    main()