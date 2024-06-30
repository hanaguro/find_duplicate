#!/usr/bin/python3

import os
import re
import sys
import fnmatch
from collections import defaultdict

PKGDIR = "/var/log/packages/"

# コマンドライン引数からパスを取得
paths = []
options = []
for arg in sys.argv[1:]:
    if arg.startswith('-'):
        options.append(arg)
    else:
        paths.append(PKGDIR + arg)

# 引数が与えられなかった場合は、pathsにPKGDIRを格納
if not paths:
    paths.append(PKGDIR)

# ヘルプメッセージを表示する関数
def print_help():
    print("使用方法1: python find_duplicate.py [オプション]")
    print("使用方法2: python find_duplicate.py [オプション] <パッケージ1> <パッケージ>")
    print("オプション:")
    print("  -a    重複するファイルを含むパッケージと重複する恐れのあるライブラリを含むパッケージの両方を表示")
    print("  -p    重複する恐れのあるライブラリを含むパッケージのみを表示")
    print("  -h    このヘルプメッセージを表示")
    sys.exit(0)

# -h オプションが指定されている場合はヘルプメッセージを表示
if '-h' in options:
    print_help()

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

# 除外するファイルパターンを読み込む
exclude_patterns_from_conf = set()
config_file = os.path.expanduser("~/.find_duplicate.conf")
if os.path.exists(config_file):
    with open(config_file, 'r') as conf:
        for line in conf:
            line = line.strip()
            if line.startswith("BLOCK="):
                exclude_patterns_from_conf.update(line.split("=")[1].split())

# パターンに一致するかどうかを確認する関数
def is_excluded(line, file_path):
    base_name = os.path.basename(file_path)
    if any(re.search(pattern, line) for pattern in exclude_patterns):
        return True
    if any(fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(base_name, pattern) for pattern in exclude_patterns_from_conf):
        return True
    return False

# ファイルを処理する関数
def process_file(file_path):
    with open(file_path, 'r') as f:
        lines = set()  # 同一ファイル内の重複行を防ぐために使用
        for line in f:
            line = line.strip()
            if is_excluded(line, file_path):
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

def print_duplicates():
    print("重複するファイル/リンク:")
    for line, files in duplicate_lines.items():
        if len(files) > 1:
            print(f"重複ファイル: /{line}")
            for file in sorted(files):
                name = os.path.basename(file)
                print(f"パッケージ: {name}")
            print("")

def print_potential_duplicates():
    print("重複の恐れがあるライブラリ (.so):")
    for base_name, file_dict in potential_duplicates.items():
        if len(file_dict) > 1:
            print(f"ベース名: /{base_name}")
            for file_path, lines in file_dict.items():
                for line in lines:
                    name = os.path.basename(file_path)
                    print(f"エントリ: /{line} ({name})")
            print("")

# 結果を表示
if "-a" in options:
    print_duplicates()
    print_potential_duplicates()
elif "-p" in options:
    print_potential_duplicates()
else:
    print_duplicates()

