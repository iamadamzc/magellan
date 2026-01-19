#!/usr/bin/env python3
"""ASCII Compliance Scanner - Finds all non-ASCII characters in source files."""

import os

files_to_scan = {
    'main.py': r'a:\1\Magellan\main.py',
    'data_handler.py': r'a:\1\Magellan\src\data_handler.py',
    'features.py': r'a:\1\Magellan\src\features.py'
}

print("=" * 70)
print("ASCII STRESS TEST PREP - COMPREHENSIVE SCAN")
print("=" * 70)
print()

total_issues = 0

for filename, filepath in files_to_scan.items():
    if not os.path.exists(filepath):
        print(f"[WARNING] {filename}: File not found")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    non_ascii_lines = []
    for i, line in enumerate(lines, 1):
        non_ascii_chars = [(pos, char, ord(char)) for pos, char in enumerate(line) if ord(char) > 127]
        if non_ascii_chars:
            non_ascii_lines.append((i, line.rstrip(), non_ascii_chars))
    
    print(f"[SCAN] {filename}: {len(non_ascii_lines)} non-ASCII lines")
    
    if non_ascii_lines:
        total_issues += len(non_ascii_lines)
        for line_num, line_content, chars in non_ascii_lines[:5]:  # Show first 5
            print(f"  Line {line_num}: {line_content[:70]}")
            for pos, char, code in chars[:3]:  # Show first 3 chars per line
                print(f"    Position {pos}: '{char}' (U+{code:04X})")
        
        if len(non_ascii_lines) > 5:
            print(f"  ... and {len(non_ascii_lines) - 5} more lines")
    
    print()

print("=" * 70)
if total_issues == 0:
    print("[OK] ALL FILES ARE ASCII-COMPLIANT")
else:
    print(f"[ACTION REQUIRED] {total_issues} lines need ASCII conversion")
print("=" * 70)
