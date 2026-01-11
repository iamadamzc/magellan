#!/usr/bin/env python3
"""ASCII Compliance Scanner - Extended scan for stress test prep."""

import os

# Extended file list including stress test files
files_to_scan = {
    'main.py': r'a:\1\Magellan\main.py',
    'data_handler.py': r'a:\1\Magellan\src\data_handler.py',
    'features.py': r'a:\1\Magellan\src\features.py',
    'backtester_pro.py': r'a:\1\Magellan\src\backtester_pro.py',
    'pnl_tracker.py': r'a:\1\Magellan\src\pnl_tracker.py',
    'optimizer.py': r'a:\1\Magellan\src\optimizer.py',
    'validation.py': r'a:\1\Magellan\src\validation.py'
}

print("=" * 70)
print("ASCII STRESS TEST PREP - FINAL VERIFICATION")
print("=" * 70)
print()

total_issues = 0
files_scanned = 0
files_clean = 0

for filename, filepath in files_to_scan.items():
    if not os.path.exists(filepath):
        print(f"[SKIP] {filename}: File not found")
        continue
    
    files_scanned += 1
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    non_ascii_lines = []
    for i, line in enumerate(lines, 1):
        non_ascii_chars = [(pos, char, ord(char)) for pos, char in enumerate(line) if ord(char) > 127]
        if non_ascii_chars:
            non_ascii_lines.append((i, line.rstrip(), non_ascii_chars))
    
    if non_ascii_lines:
        print(f"[ALERT] {filename}: {len(non_ascii_lines)} non-ASCII lines")
        total_issues += len(non_ascii_lines)
        for line_num, line_content, chars in non_ascii_lines[:3]:
            print(f"  Line {line_num}: {line_content[:60]}")
            for pos, char, code in chars[:2]:
                print(f"    Position {pos}: '{char}' (U+{code:04X})")
        if len(non_ascii_lines) > 3:
            print(f"  ... and {len(non_ascii_lines) - 3} more lines")
    else:
        print(f"[OK] {filename}: ASCII-compliant")
        files_clean += 1
    
    print()

print("=" * 70)
print("FINAL VERIFICATION SUMMARY")
print("=" * 70)
print(f"Files scanned: {files_scanned}")
print(f"Files clean: {files_clean}")
print(f"Total non-ASCII lines: {total_issues}")
print()

if total_issues == 0:
    print("[OK] ALL FILES ARE ASCII-COMPLIANT - READY FOR STRESS TEST")
else:
    print(f"[ACTION REQUIRED] {total_issues} lines need ASCII conversion")

print("=" * 70)
