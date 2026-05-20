---
name: read_file_and_add
description: add all numbers in a text file by 10 and save to a new file. Use when user mentions read a file add numbers by 10, process number file, batch calculation.

input_params:
  - name: input_file
    type: string
    required: true
    description: 输入文件路径（包含数字的文本文件）

  - name: output_file
    type: string
    required: true
    description: 输出文件路径

output_params:
  - name: output
    type: csv_file
    description: 处理后的文本文件
---

# Add Numbers by 10

Add all numbers in a text file by 10 and save to a new file.

## Features

- **Auto-detect delimiters**: Supports comma, space, newline, tab and other separators
- **Preserve original format**: Automatically detect and maintain original separator format
- **Flexible input**: Support command line arguments or interactive input
- **Error handling**: Validate file existence and number format

## Usage

### Method 1: Command Line Arguments (Recommended)

Call skill directly with input and output file paths:

```
/read_file_and_add input.txt output.txt
```

**Parameters**:
- `input.txt`: Text file containing numbers (e.g., `1,2,3` or `1 2 3` or one number per line)
- `output.txt`: Output file path for processed results

### Method 2: Interactive Input

Call skill without parameters, then follow prompts:

```
/read_file_and_add
```

Then enter:
1. Input file path
2. Output file path

## Supported Delimiters

Automatically detects:
- Comma (`,`) - e.g., `1,2,3,4`
- Space (` `) - e.g., `1 2 3 4`
- Newline - one number per line
- Tab (`\t`) - e.g., `1	2	3`
- Multiple spaces - automatically handled

## Examples

### Example 1: Comma Separated
**Input file content**:
```
1,2,3,4,5
```

**Output file content**:
```
11,12,13,14,15
```

### Example 2: Space Separated
**Input file content**:
```
1.5 2.3 3.7
```

**Output file content**:
```
10.5 12.3 13.7
```

### Example 3: Newline Separated
**Input file content**:
```
10
20
30
```

**Output file content**:
```
20
30
40
```

### Example 4: Mixed Format
**Input file content**:
```
1,2 3
4,5
```

**Output file content**:
```
11,12 13
14,15
```

## Output Format

Output file preserves same format as input:
- If input is single line with commas, output is single line with commas
- If input is one number per line, output is one number per line
- If input has mixed structure, output maintains same structure

## Error Handling

Errors and stops on:
- Input file does not exist
- Input file is empty
- File contains non-numeric characters (letters, special symbols)

## Technical Implementation

Uses Python script `scripts/process_numbers.py` to process file content, automatically detect delimiter type and maintain format consistency.
use command `python scripts/process_numbers.py <input_file_path> <output_file_path>`
