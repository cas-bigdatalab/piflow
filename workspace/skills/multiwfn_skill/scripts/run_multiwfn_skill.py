#!/usr/bin/env python3
"""
Execute Multiwfn wavefunction analysis program.
Supports extracting HOMO/LUMO, surface analysis, population analysis from .mout files.
"""

import argparse
import os
import subprocess
import sys
import zipfile
import json
import re
from pathlib import Path


def find_multiwfn_path():
    multiwfn_root = os.environ.get('MULTIWFN_ROOT')
    if multiwfn_root and os.path.exists(multiwfn_root):
        print(f"Using MULTIWFN_ROOT: {multiwfn_root}")
        return multiwfn_root
    
    default_paths = [
        os.path.expandvars("$HOME/Multiwfn_3.8_dev_bin_Linux_noGUI"),
        "/opt/Multiwfn_3.8_dev_bin_Linux_noGUI",
        "/usr/local/Multiwfn_3.8_dev_bin_Linux_noGUI",
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            print(f"Found Multiwfn at: {path}")
            return path
    
    return None


def validate_multiline_param(param_str):
    if not param_str:
        return ""
    
    param_str = param_str.replace('\r\n', '\n').replace('\r', '\n')
    lines = param_str.split('\n')
    valid_lines = [line.strip() for line in lines if line.strip()]
    
    return '\n'.join(valid_lines)


def parse_multiwfn_mout(mout_path):
    summary = {
        "tool": "Multiwfn",
        "inputPath": "",
        "moutPath": str(mout_path),
        "normalExit": False,
        "formula": "",
        "atomCount": 0,
        "molecularMass": None,
        "electronCount": None,
        "numThreads": None,
        "wavefunctionType": "",
        "orbitals": {},
        "surfaceAnalyses": [],
        "populationAnalysis": {"chargeModels": []},
        "atomSurfaceContributions": []
    }

    if not mout_path.exists():
        return summary

    with open(mout_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    for line in content.split('\n'):
        match = re.search(r'Number of parallel threads:\s+(\d+)', line)
        if match:
            summary["numThreads"] = int(match.group(1))

        match = re.search(r'Total/Alpha/Beta electrons:\s+([\d.]+)', line)
        if match:
            summary["electronCount"] = float(match.group(1))

        match = re.search(r'Formula:\s+([A-Za-z0-9\s]+?)\s+Total', line)
        if match:
            summary["formula"] = match.group(1).strip()

        match = re.search(r'Total atoms:\s+(\d+)', line)
        if match:
            summary["atomCount"] = int(match.group(1))

        match = re.search(r'Molecule weight:\s+([\d.]+)\s+Da', line)
        if match:
            summary["molecularMass"] = float(match.group(1))

        match = re.search(r'This is a\s+(.+?)\s+wavefunction', line)
        if match:
            summary["wavefunctionType"] = match.group(1).strip()

        match = re.search(r'Note: Orbital\s+(\d+)\s+is HOMO, energy:\s+([\-\d.]+)\s+a\.u\.\s+([\-\d.]+)\s+eV', line)
        if match and "orbitals" in summary:
            if "homo" not in summary["orbitals"]:
                summary["orbitals"]["homo"] = {
                    "orbitalIndex": int(match.group(1)),
                    "energyAu": float(match.group(2)),
                    "energyEv": float(match.group(3))
                }

        match = re.search(r'Orbital\s+(\d+)\s+is LUMO, energy:\s+([\-\d.]+)\s+a\.u\.\s+([\-\d.]+)\s+eV', line)
        if match and "orbitals" in summary:
            if "lumo" not in summary["orbitals"]:
                summary["orbitals"]["lumo"] = {
                    "orbitalIndex": int(match.group(1)),
                    "energyAu": float(match.group(2)),
                    "energyEv": float(match.group(3))
                }

        match = re.search(r'HOMO-LUMO gap:\s+([\-\d.]+)\s+a\.u\.\s+([\-\d.]+)\s+eV\s+([\-\d.]+)\s+kJ/mol', line)
        if match and "orbitals" in summary:
            summary["orbitals"]["gap"] = {
                "energyAu": float(match.group(1)),
                "energyEv": float(match.group(2)),
                "energyKjMol": float(match.group(3))
            }

    surface_pattern = r'================= Summary of surface analysis =================\s+Volume:\s+([\-\d.]+)\s+Bohr\^3\s+\(\s+([\-\d.]+)\s+Angstrom\^3\)\s+Estimated density according to mass and volume \(M/V\):\s+([\-\d.]+)\s+g/cm\^3\s+Minimal value:\s+([\-\d.]+[^\n]*)\s+Maximal value:\s+([\-\d.]+[^\n]*)\s+Overall surface area:\s+([\-\d.]+)\s+Bohr\^2\s+\(\s+([\-\d.]+)\s+Angstrom\^2\)\s+Positive surface area:\s+([\-\d.]+)\s+Bohr\^2\s+\(\s+([\-\d.]+)\s+Angstrom\^2\)\s+Negative surface area:\s+([\-\d.]+)\s+Bohr\^2\s+\(\s+([\-\d.]+)\s+Angstrom\^2\)\s+Overall average value:\s+([\-\d.]+[^\n]*)\s+Positive average value:\s+([\-\d.]+[^\n]*)\s+Negative average value:\s+([^\n]*)\s+Overall variance.*:\s+([\-\d.]+[^\n]*)\s+Positive variance:\s+([\-\d.]+[^\n]*)\s+Negative variance:\s+([^\n]*)\s+Overall skewness:\s+([\-\d.]+)\s+Positive skewness:\s+([\-\d.]+)'
    surface_matches = re.findall(surface_pattern, content, re.DOTALL)
    
    for sm in surface_matches:
        surface_analysis = {
            "volumeBohr3": float(sm[0]),
            "volumeAngstrom3": float(sm[1]),
            "estimatedDensityGCm3": float(sm[2]),
            "minimalValue": float(sm[3].split()[0]),
            "maximalValue": float(sm[4].split()[0]),
            "overallAreaBohr2": float(sm[5]),
            "overallAreaAngstrom2": float(sm[6]),
            "positiveAreaBohr2": float(sm[7]),
            "positiveAreaAngstrom2": float(sm[8]),
            "negativeAreaBohr2": float(sm[9]),
            "negativeAreaAngstrom2": float(sm[10]),
            "overallAverage": float(sm[11].split()[0]),
            "positiveAverage": float(sm[12].split()[0]),
            "negativeAverage": None if "NaN" in sm[13] else float(sm[13].split()[0]),
            "overallVariance": float(sm[14].split()[0]),
            "positiveVariance": float(sm[15].split()[0]),
            "negativeVariance": None if "NaN" in sm[16] else float(sm[16].split()[0]),
            "overallSkewness": float(sm[17]),
            "positiveSkewness": float(sm[18])
        }
        summary["surfaceAnalyses"].append(surface_analysis)

    in_atom_surface_section = False
    for line in content.split('\n'):
        if "All/Positive/Negative area (Ang^2)" in line and "Minimal value" in line:
            in_atom_surface_section = True
            continue
        if in_atom_surface_section:
            if not line.strip():
                in_atom_surface_section = False
                continue
            match = re.match(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)', line)
            if match:
                summary["atomSurfaceContributions"].append({
                    "atomIndex": int(match.group(1)),
                    "allAreaAngstrom2": float(match.group(2)),
                    "positiveAreaAngstrom2": float(match.group(3)),
                    "negativeAreaAngstrom2": float(match.group(4)),
                    "minimalValue": float(match.group(5)),
                    "maximalValue": float(match.group(6))
                })

    mulliken_pattern = r'(Mulliken atom & basis function population analysis|Mulliken charges:)\s*(.*?)(?=\n\n|\Z)'
    mulliken_matches = re.findall(mulliken_pattern, content, re.DOTALL)
    for match in mulliken_matches:
        charges = []
        lines = match[1].split('\n')
        for line in lines:
            match = re.match(r'^\s*(\d+)\s+([A-Za-z]+)\s+([\-\d.]+)', line)
            if match:
                charges.append({
                    "atomIndex": int(match.group(1)),
                    "element": match.group(2),
                    "charge": float(match.group(3))
                })
        if charges:
            summary["populationAnalysis"]["chargeModels"].append({
                "model": "Mulliken",
                "charges": charges
            })

    hirshfeld_pattern = r'Hirshfeld charge of atom\s+(\d+)\(([A-Za-z]+\s*)\)\s+is\s+([\-\d.]+)'
    hirshfeld_matches = re.findall(hirshfeld_pattern, content)
    if hirshfeld_matches:
        charges = []
        for match in hirshfeld_matches:
            charges.append({
                "atomIndex": int(match[0]),
                "element": match[1].strip(),
                "charge": float(match[2])
            })
        summary["populationAnalysis"]["chargeModels"].append({
            "model": "Hirshfeld",
            "charges": charges
        })

    adch_pattern = r'---------- Atomic dipole moment corrected \(ADC\) charges ----------(.*?)(?=\n\n|\Z)'
    adch_match = re.search(adch_pattern, content, re.DOTALL)
    if adch_match:
        lines = adch_match.group(1).split('\n')
        charges = []
        for line in lines:
            match = re.match(r'\s*Atom:\s*(\d+)([A-Za-z]+)\s+Corrected charge:\s+([\-\d.]+)', line)
            if match:
                charges.append({
                    "atomIndex": int(match.group(1)),
                    "element": match.group(2),
                    "charge": float(match.group(3))
                })
        if charges:
            summary["populationAnalysis"]["chargeModels"].append({
                "model": "ADCH",
                "charges": charges
            })

    if "q" in content and "Exit program gracefully" in content:
        summary["normalExit"] = True

    if not summary["orbitals"]:
        summary["orbitals"] = {}

    return summary


def main():
    parser = argparse.ArgumentParser(
        description='Execute Multiwfn wavefunction analysis program',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input_path', required=True, help='Input file path (.fchk, .wfn, .wfx, etc.)')
    parser.add_argument('--other_param', default='', help='Multi-line string of Multiwfn commands')
    parser.add_argument('--threads', type=int, default=32, help='Number of threads')
    parser.add_argument('--multiwfn_path', help='Explicit path to Multiwfn installation')
    parser.add_argument('--output_dir', required=True, help='Output working directory')
    parser.add_argument('--mout_output_path', required=True, help='Output mout file path')
    parser.add_argument('--compressed_output_path', required=True, help='Output zip file path')
    
    args = parser.parse_args()

    input_path = Path(args.input_path).resolve()
    mout_output_path = Path(args.mout_output_path)
    compressed_output_path = Path(args.compressed_output_path)
    output_dir = Path(args.output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    stderr_content = ""
    stderr_log_path = output_dir / 'stderr.log'

    if not input_path.exists():
        error_output = {
            "status": "failed",
            "mout_output_path": "",
            "compressed_output_path": "",
            "errorMessage": f"Input file not found: {args.input_path}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)

    multiwfn_path = None
    if args.multiwfn_path:
        multiwfn_path = Path(args.multiwfn_path).resolve()
    else:
        multiwfn_path = find_multiwfn_path()
        if multiwfn_path:
            multiwfn_path = Path(multiwfn_path)
    
    if not multiwfn_path or not multiwfn_path.exists():
        error_output = {
            "status": "failed",
            "mout_output_path": "",
            "compressed_output_path": "",
            "errorMessage": "Multiwfn installation not found. Set MULTIWFN_ROOT env var or use --multiwfn-path"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    multiwfn_exe = multiwfn_path / "Multiwfn_noGUI"
    if not multiwfn_exe.exists():
        error_output = {
            "status": "failed",
            "mout_output_path": "",
            "compressed_output_path": "",
            "errorMessage": f"Multiwfn executable not found: {multiwfn_exe}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    print(f"Multiwfn executable: {multiwfn_exe}")

    other_param = validate_multiline_param(args.other_param)
    if other_param:
        cmd_count = len(other_param.split('\n'))
        print(f"Command sequence ({cmd_count} commands):")
        for i, line in enumerate(other_param.split('\n'), 1):
            print(f"  {i}: {line}")

    input_dir = str(input_path.parent)
    shell_command = f"""cd "{input_dir}"; export OMP_STACKSIZE=200M; export Multiwfnpath="{multiwfn_path}"; export PATH="$PATH:{multiwfn_path}"; "{multiwfn_exe}" "{input_path}" -nt {args.threads} > "{mout_output_path}" <<EOF
{other_param}
EOF"""
    
    print(f"\nExecuting Multiwfn...")
    
    try:
        result = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            if result.stdout.strip():
                print(f"STDOUT:\n{result.stdout[:500]}..." if len(result.stdout) > 500 else f"STDOUT:\n{result.stdout}")
        if result.stderr:
            if result.stderr.strip():
                print(f"STDERR:\n{result.stderr[:500]}..." if len(result.stderr) > 500 else f"STDERR:\n{result.stderr}", file=sys.stderr)
                stderr_content += "Multiwfn STDERR:\n" + result.stderr + "\n"
        
        if not mout_output_path.exists():
            stderr_content += "Error: Output file was not created\n"
            with open(stderr_log_path, 'w', encoding='utf-8') as f:
                f.write(stderr_content)
            
            with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if stderr_log_path.exists():
                    zf.write(stderr_log_path, stderr_log_path.name)
            
            error_output = {
                "status": "failed",
                "mout_output_path": "",
                "compressed_output_path": str(compressed_output_path),
                "errorMessage": "Output file was not created"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
        
        file_size = mout_output_path.stat().st_size
        print(f"Output file size: {file_size} bytes")
        if file_size == 0:
            stderr_content += "Warning: Output file is empty\n"

    except subprocess.CalledProcessError as e:
        stderr_content += f"Error executing Multiwfn: {e}\n"
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
            "mout_output_path": "",
            "compressed_output_path": str(compressed_output_path),
            "errorMessage": f"Error executing Multiwfn: {e}"
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
            "mout_output_path": "",
            "compressed_output_path": str(compressed_output_path),
            "errorMessage": f"Unexpected error: {e}"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)

    summary = parse_multiwfn_mout(mout_output_path)
    summary["inputPath"] = str(input_path)
    
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    if stderr_content:
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)

    with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if summary_path.exists():
            zf.write(summary_path, summary_path.name)
        if stderr_log_path.exists():
            zf.write(stderr_log_path, stderr_log_path.name)

    success_output = {
        "status": "success",
        "mout_output_path": str(mout_output_path),
        "compressed_output_path": str(compressed_output_path)
    }
    print(json.dumps(success_output, ensure_ascii=False))


if __name__ == "__main__":
    main()