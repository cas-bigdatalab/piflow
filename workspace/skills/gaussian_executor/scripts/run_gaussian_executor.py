#!/usr/bin/env python3
"""
Execute Gaussian 16 quantum chemistry calculation.
Supports DFT structure optimization, frequency analysis, and single point energy calculation.
Compatible with both Windows and Linux.
"""

import argparse
import os
import subprocess
import sys
import zipfile
import json
import shutil
import re
from pathlib import Path


def parse_gaussian_log(log_path):
    summary = {
        "tool": "Gaussian16",
        "task": "unknown",
        "normalTermination": False,
        "logPath": str(log_path),
        "chkPath": "",
        "fchkPath": "",
    }
    
    energy_info = {}
    dipole_info = {}
    mulliken_charges = []
    frequency_analysis = None
    
    frequencies = []
    reduced_masses = []
    force_constants = []
    ir_intensities = []
    thermochemistry = {}
    
    in_mulliken_section = False
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "SCF Done:" in line:
                match = re.search(r'SCF Done:\s+E\(([^)]+)\)\s*=\s*([\-\d\.]+)', line)
                if match:
                    energy_info = {
                        "method": match.group(1),
                        "energyHartree": float(match.group(2))
                    }
            
            elif "Dipole moment" in line and "Debye" in line:
                dipole_lines = []
                for _ in range(2):
                    next_line = next(f, '')
                    dipole_lines.append(next_line)
                dipole_text = ''.join(dipole_lines)
                match = re.search(r'X=\s*([\-\d\.]+)\s+Y=\s*([\-\d\.]+)\s+Z=\s*([\-\d\.]+)\s+Tot=\s*([\-\d\.]+)', dipole_text)
                if match:
                    dipole_info = {
                        "dipoleDebye": {
                            "x": float(match.group(1)),
                            "y": float(match.group(2)),
                            "z": float(match.group(3)),
                            "total": float(match.group(4))
                        }
                    }
            
            elif "Mulliken charges:" in line:
                in_mulliken_section = True
                continue
            
            elif in_mulliken_section:
                line = line.strip()
                if not line or "Sum of Mulliken charges" in line or "Mulliken atomic charges" in line:
                    in_mulliken_section = False
                    continue
                match = re.match(r'^\s*(\d+)\s+([A-Za-z]+)\s+([\-\d\.]+)', line)
                if match:
                    mulliken_charges.append({
                        "atomIndex": int(match.group(1)),
                        "element": match.group(2),
                        "charge": float(match.group(3))
                    })
            
            elif "Frequencies --" in line:
                freq_values = re.findall(r'-?\d+\.\d+', line)
                frequencies.extend([float(v) for v in freq_values])
            
            elif "Red. masses --" in line:
                mass_values = re.findall(r'-?\d+\.\d+', line)
                reduced_masses.extend([float(v) for v in mass_values])
            
            elif "Frc consts  --" in line:
                force_values = re.findall(r'-?\d+\.\d+', line)
                force_constants.extend([float(v) for v in force_values])
            
            elif "IR Inten    --" in line:
                ir_values = re.findall(r'-?\d+\.\d+', line)
                ir_intensities.extend([float(v) for v in ir_values])
            
            elif "Zero-point correction=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["zeroPointCorrectionHartree"] = float(match.group(1))
            
            elif "Thermal correction to Energy=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["thermalCorrectionToEnergyHartree"] = float(match.group(1))
            
            elif "Thermal correction to Enthalpy=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["thermalCorrectionToEnthalpyHartree"] = float(match.group(1))
            
            elif "Thermal correction to Gibbs Free Energy=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["thermalCorrectionToGibbsFreeEnergyHartree"] = float(match.group(1))
            
            elif "Sum of electronic and zero-point Energies=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["electronicAndZeroPointEnergyHartree"] = float(match.group(1))
            
            elif "Sum of electronic and thermal Energies=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["electronicAndThermalEnergyHartree"] = float(match.group(1))
            
            elif "Sum of electronic and thermal Enthalpies=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["electronicAndThermalEnthalpyHartree"] = float(match.group(1))
            
            elif "Sum of electronic and thermal Free Energies=" in line:
                match = re.search(r'=\s*([\-\d\.]+)', line)
                if match:
                    thermochemistry["electronicAndThermalFreeEnergyHartree"] = float(match.group(1))
            
            elif "Normal termination of Gaussian" in line:
                summary["normalTermination"] = True
            
            elif "opt" in line.lower() and not "optimize" in line.lower():
                if "freq" in line.lower():
                    summary["task"] = "opt_freq"
                else:
                    summary["task"] = "opt"
            elif "freq" in line.lower() and not "frequency" in line.lower():
                if summary["task"] == "unknown":
                    summary["task"] = "freq"
            elif "sp" in line.lower() and "single" in line.lower():
                if summary["task"] == "unknown":
                    summary["task"] = "sp"
    
    if energy_info:
        summary["energy"] = energy_info
    
    if dipole_info:
        summary.update(dipole_info)
    
    if mulliken_charges:
        atom_count = len(mulliken_charges)
        if atom_count > 0 and atom_count % 8 == 0:
            summary["mullikenCharges"] = mulliken_charges[-8:]
        else:
            summary["mullikenCharges"] = mulliken_charges
    
    if frequencies:
        imaginary_freqs = [f for f in frequencies if f < 0]
        frequency_analysis = {
            "frequenciesCm-1": frequencies,
            "imaginaryFrequenciesCm-1": imaginary_freqs,
            "imaginaryFrequencyCount": len(imaginary_freqs),
            "hasImaginaryFrequency": len(imaginary_freqs) > 0,
            "reducedMasses": reduced_masses,
            "forceConstants": force_constants,
            "irIntensities": ir_intensities
        }
        if thermochemistry:
            frequency_analysis["thermochemistry"] = thermochemistry
        summary["frequencyAnalysis"] = frequency_analysis
    
    return summary


def main():
    parser = argparse.ArgumentParser(description='Execute Gaussian 16 quantum chemistry calculation')
    parser.add_argument('--input_path', required=True, help='Input .gjf file path')
    parser.add_argument('--output_dir', required=True, help='Output working directory')
    parser.add_argument('--log_output_path', required=True, help='Log file output path')
    parser.add_argument('--chk_output_path', required=True, help='Chk file output path')
    parser.add_argument('--compressed_output_path', required=True, help='Compressed output zip path')
    parser.add_argument('--other_param', default='', help='Additional parameters')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_path)
    if not input_path.exists():
        error_output = {
            "status": "failed",
            "log_output_path": "",
            "chk_output_path": "",
            "compressed_output_path": "",
            "errorMessage": f"Input file '{args.input_path}' does not exist"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_output_path = Path(args.log_output_path)
    chk_output_path = Path(args.chk_output_path)
    compressed_output_path = Path(args.compressed_output_path)
    stderr_log_path = output_dir / 'stderr.log'
    summary_path = output_dir / 'summary.json'
    
    input_without_ext = input_path.with_suffix('')
    
    stderr_content = ""
    
    if os.name == 'nt':
        g16_path = None
        if os.environ.get('g16root'):
            g16_path = Path(os.environ['g16root']) / 'g16.exe'
        else:
            for candidate in [Path('C:/G16W/g16.exe'), Path('C:/gaussian/g16/g16.exe'), Path('C:/g16/g16.exe')]:
                if candidate.exists():
                    g16_path = candidate
                    break
        
        if g16_path is None or not g16_path.exists():
            error_output = {
                "status": "failed",
                "log_output_path": "",
                "chk_output_path": "",
                "compressed_output_path": "",
                "errorMessage": "Gaussian g16 not found. Please set g16root environment variable or install Gaussian."
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
        
        gaussian_dir = g16_path.parent
        
        env = os.environ.copy()
        env['g16root'] = str(gaussian_dir)
        env['GAUSS_EXEDIR'] = str(gaussian_dir)
        env['GAUSS_SCRDIR'] = str(output_dir / 'scr')
        
        os.makedirs(env['GAUSS_SCRDIR'], exist_ok=True)
        
        cmd = [str(g16_path), str(input_path), str(log_output_path)]
        print(f"$$command: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr, file=sys.stderr)
                stderr_content += "g16 STDERR:\n" + result.stderr + "\n"
            
            formchk_path = gaussian_dir / 'formchk.exe'
            if formchk_path.exists():
                chk_file = input_without_ext.with_suffix('.chk')
                if chk_file.exists():
                    formchk_cmd = [str(formchk_path), str(chk_file)]
                    print(f"$$command: {' '.join(formchk_cmd)}")
                    formchk_result = subprocess.run(
                        formchk_cmd,
                        capture_output=True,
                        text=True,
                        env=env
                    )
                    if formchk_result.stdout:
                        print("formchk STDOUT:", formchk_result.stdout)
                    if formchk_result.stderr:
                        print("formchk STDERR:", formchk_result.stderr, file=sys.stderr)
                        stderr_content += "formchk STDERR:\n" + formchk_result.stderr + "\n"
        except subprocess.CalledProcessError as e:
            stderr_content += f"Error executing Gaussian command: {e}\n"
            if e.stdout:
                stderr_content += f"STDOUT: {e.stdout}\n"
            if e.stderr:
                stderr_content += f"STDERR: {e.stderr}\n"
            with open(stderr_log_path, 'w', encoding='utf-8') as f:
                f.write(stderr_content)
            
            with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if log_output_path.exists():
                    zf.write(log_output_path, log_output_path.name)
                if stderr_log_path.exists():
                    zf.write(stderr_log_path, stderr_log_path.name)
            
            error_output = {
                "status": "failed",
                "log_output_path": str(log_output_path),
                "chk_output_path": "",
                "compressed_output_path": str(compressed_output_path),
                "errorMessage": f"Error executing Gaussian command: {e}"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
        except Exception as e:
            stderr_content += f"Unexpected error: {e}\n"
            with open(stderr_log_path, 'w', encoding='utf-8') as f:
                f.write(stderr_content)
            
            with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if log_output_path.exists():
                    zf.write(log_output_path, log_output_path.name)
                if stderr_log_path.exists():
                    zf.write(stderr_log_path, stderr_log_path.name)
            
            error_output = {
                "status": "failed",
                "log_output_path": str(log_output_path),
                "chk_output_path": "",
                "compressed_output_path": str(compressed_output_path),
                "errorMessage": f"Unexpected error: {e}"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
    else:
        g16root = os.environ.get('g16root', '$HOME/gaussian')
        gauss_exedir = os.environ.get('GAUSS_EXEDIR', f'{g16root}/g16')
        gauss_scrdir = os.environ.get('GAUSS_SCRDIR', f'{g16root}/scr')
        
        shell_command = f"source ~/.bashrc; export g16root={g16root}; export GAUSS_EXEDIR={gauss_exedir}; export GAUSS_SCRDIR={gauss_scrdir}; {gauss_exedir}/g16 < {args.input_path} > {args.log_output_path}; {gauss_exedir}/formchk {input_without_ext}.chk"
        print(f"$$command: {shell_command}")
        
        try:
            result = subprocess.run(
                shell_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr, file=sys.stderr)
                stderr_content += "shell STDERR:\n" + result.stderr + "\n"
        except subprocess.CalledProcessError as e:
            stderr_content += f"Error executing Gaussian command: {e}\n"
            if e.stdout:
                stderr_content += f"STDOUT: {e.stdout}\n"
            if e.stderr:
                stderr_content += f"STDERR: {e.stderr}\n"
            with open(stderr_log_path, 'w', encoding='utf-8') as f:
                f.write(stderr_content)
            
            with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if log_output_path.exists():
                    zf.write(log_output_path, log_output_path.name)
                if stderr_log_path.exists():
                    zf.write(stderr_log_path, stderr_log_path.name)
            
            error_output = {
                "status": "failed",
                "log_output_path": str(log_output_path),
                "chk_output_path": "",
                "compressed_output_path": str(compressed_output_path),
                "errorMessage": f"Error executing Gaussian command: {e}"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
        except Exception as e:
            stderr_content += f"Unexpected error: {e}\n"
            with open(stderr_log_path, 'w', encoding='utf-8') as f:
                f.write(stderr_content)
            
            with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if log_output_path.exists():
                    zf.write(log_output_path, log_output_path.name)
                if stderr_log_path.exists():
                    zf.write(stderr_log_path, stderr_log_path.name)
            
            error_output = {
                "status": "failed",
                "log_output_path": str(log_output_path),
                "chk_output_path": "",
                "compressed_output_path": str(compressed_output_path),
                "errorMessage": f"Unexpected error: {e}"
            }
            print(json.dumps(error_output, ensure_ascii=False))
            sys.exit(1)
    
    chk_source = None
    input_basename = input_path.stem
    possible_chk_paths = [
        input_without_ext.with_suffix('.chk'),
        Path.cwd() / f"{input_basename}.chk",
        output_dir / f"{input_basename}.chk",
        log_output_path.parent / f"{input_basename}.chk"
    ]
    
    for candidate in possible_chk_paths:
        if candidate.exists():
            chk_source = candidate
            break
    
    if chk_source is not None:
        shutil.move(str(chk_source), str(chk_output_path))
    else:
        stderr_content += "chk file not generated\n"
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)
        
        with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if log_output_path.exists():
                zf.write(log_output_path, log_output_path.name)
            if stderr_log_path.exists():
                zf.write(stderr_log_path, stderr_log_path.name)
        
        error_output = {
            "status": "failed",
            "log_output_path": str(log_output_path),
            "chk_output_path": "",
            "compressed_output_path": str(compressed_output_path),
            "errorMessage": "chk file not generated"
        }
        print(json.dumps(error_output, ensure_ascii=False))
        sys.exit(1)
    
    if stderr_content:
        with open(stderr_log_path, 'w', encoding='utf-8') as f:
            f.write(stderr_content)
    
    if log_output_path.exists():
        summary = parse_gaussian_log(log_output_path)
        summary["chkPath"] = str(chk_output_path)
        fchk_file = input_without_ext.with_suffix('.fchk')
        if fchk_file.exists():
            summary["fchkPath"] = str(fchk_file)
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    with zipfile.ZipFile(compressed_output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        if log_output_path.exists():
            zf.write(log_output_path, log_output_path.name)
        if chk_output_path.exists():
            zf.write(chk_output_path, chk_output_path.name)
        fchk_file = input_without_ext.with_suffix('.fchk')
        if fchk_file.exists():
            zf.write(fchk_file, fchk_file.name)
        if summary_path.exists():
            zf.write(summary_path, summary_path.name)
        if stderr_log_path.exists():
            zf.write(stderr_log_path, stderr_log_path.name)
    
    success_output = {
        "status": "success",
        "log_output_path": str(log_output_path),
        "chk_output_path": str(chk_output_path),
        "compressed_output_path": str(compressed_output_path)
    }
    print(json.dumps(success_output, ensure_ascii=False))


if __name__ == "__main__":
    main()
