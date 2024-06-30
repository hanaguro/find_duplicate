import os
import re
import sys
from collections import defaultdict

# コマンドライン引数からパスを取得
paths = sys.argv[1:]

# 重複行を保持する辞書
duplicate_lines = defaultdict(set)

# .soで終わる行を保持する辞書
potential_duplicates = defaultdict(lambda: defaultdict(set))

# 除外するパターン
exclude_patterns = [
    r"^PACKAGE NAME:",
    r"^COMPRESSED PACKAGE SIZE:",
    r"^UNCOMPRESSED PACKAGE SIZE:",
    r"^PACKAGE LOCATION:",
    r"^PACKAGE DESCRIPTION:",
    r"^FILE LIST:",
    r"^install/", 
    r".*/$"
]

# パターンに一致するかどうかを確認する関数
def is_excluded(line):
    return any(re.search(pattern, line) for pattern in exclude_patterns)

# ファイルを処理する関数
def process_file(file_path):
    with open(file_path, 'r') as f:
        lines = set()  # 同一ファイル内の重複行を防ぐために使用
        for line in f:
            line = line.strip()
            if is_excluded(line):
                continue
            if line not in lines:
                duplicate_lines[line].add(file_path)
                lines.add(line)
                if re.search(r'\.so(\.[0-9]+)*$', line):
                    base_name = re.sub(r'\.so(\.[0-9]+)*$', '.so', line)
                    potential_duplicates[base_name][file_path].add(line)

# 各ファイルを処理
for path in paths:
    if os.path.isfile(path):
        process_file(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                process_file(os.path.join(root, file))

# 重複する行を表示
print("重複するファイル/リンク:")
for line, files in duplicate_lines.items():
    if len(files) > 1:
        print(f"重複行: {line}")
        print(f"ファイル: {' '.join(sorted(files))}\n")

# 重複の恐れがある行を表示
print("重複の恐れがあるファイル/リンク (.so):")
for base_name, file_dict in potential_duplicates.items():
    if len(file_dict) > 1:
        print(f"ベース名: {base_name}")
        for file_path, lines in file_dict.items():
            for line in lines:
                print(f"エントリ: {line} ({file_path})")
        print("")

