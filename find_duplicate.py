#!/usr/bin/python3

import os
import re
import sys
import fnmatch
import subprocess
from collections import defaultdict

PKGDIR = "/var/log/packages/"

# コマンドライン引数からパスを取得
paths = []
options = []
archive_file = None

i = 1
while i < len(sys.argv):
    arg = sys.argv[i]
    if arg.startswith('-'):
        if 'd' in arg:
            if arg == '-d':                         # 引数が完全に-d
                archive_file = sys.argv[i + 1]      # 次の引数を archive_file に格納
                i += 1                              # 次の引数をスキップ
            else:
                # Extract the archive file argument when combined with other options
                idx = arg.index('d')
                if len(arg) > idx + 1:              # arg 内で d の後ろに引数が続く
                    archive_file = arg[idx + 1:]    # arg 内のd以降の文字列を archive_file に格納
                else:
                    archive_file = sys.argv[i + 1]  # 次の引数を archive_file に格納
                    i += 1                          # 次の引数をスキップ
        if 'a' in arg:
            options.append('a')
        if 'p' in arg:
            options.append('p')
    else:
        paths.append(PKGDIR + arg)
    i += 1

# 引数が与えられなかった場合は、pathsにPKGDIRを格納
if not paths:
    paths.append(PKGDIR)

# ヘルプメッセージを表示する関数
def print_help():
    print("使用方法1: python find_duplicate.py [オプション]")
    print("使用方法2: python find_duplicate.py [オプション] <パッケージ1> <パッケージ2>")
    print("使用方法3: python find_duplicate.py -d <パッケージ>")
    print("オプション:")
    print("  -a    重複するファイルを含むパッケージと重複する恐れのあるライブラリを含むパッケージの両方を表示")
    print("  -p    重複する恐れのあるライブラリを含むパッケージのみを表示")
    print("  -d <package>    指定されたPlamoパッケージと比較")
    print("  -h    このヘルプメッセージを表示")
    sys.exit(0)

# -h オプションが指定されている場合はヘルプメッセージを表示
if 'h' in options:
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

# 除外するパターンに一致するかどうかを確認する関数
def is_excluded(line, file_path):
    base_name = os.path.basename(file_path)
    if any(re.search(pattern, line) for pattern in exclude_patterns):
        return True
    if any(fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(base_name, pattern) for pattern in exclude_patterns_from_conf):
        return True
    return False

# ファイルを処理する関数
def process_file(file_path, base_path=""):
    with open(file_path, 'r') as f:
        lines = set()  # 同一ファイル内の重複行を防ぐために使用
        for line in f:
            line = line.strip()
            if is_excluded(line, file_path):
                continue
            full_line = os.path.join(base_path, line)
            if full_line not in lines:
                duplicate_lines[full_line].add(file_path)
                lines.add(full_line)
                if re.search(r'\.so(\.[0-9]+)*$', line):
                    base_name = re.sub(r'\.so(\.[0-9]+)*$', '.so', line)
                    potential_duplicates[base_name][file_path].add(full_line)

# アーカイブファイルを処理する関数
def process_archive(archive_path):
    try:
        output = subprocess.check_output(['tar', '-tf', archive_path], text=True)
        for line in output.splitlines():
            line = line.strip()
            if is_excluded(line, line):
                continue
            duplicate_lines[line].add(f"PACKAGE:{archive_path}")
            if re.search(r'\.so(\.[0-9]+)*$', line):
                base_name = re.sub(r'\.so(\.[0-9]+)*$', '.so', line)
                potential_duplicates[base_name][f"PACKAGE:{archive_path}"].add(line)
    except subprocess.CalledProcessError as e:
        print(f"パッケージの解析中に問題が発生しました: {archive_path}: {e}")
        sys.exit(1)

# 各ファイルを処理
for path in paths:
    if os.path.isfile(path):
        process_file(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                process_file(os.path.join(root, file))

# アーカイブファイルを処理
if archive_file:
    process_archive(archive_file)

def print_duplicates(filter_archive=None):
    print("重複するファイル/リンク:")
    for line, files in duplicate_lines.items():
        if len(files) > 1:
            if filter_archive and not any(f"PACKAGE:{filter_archive}" in file for file in files):
                continue
            print(f"重複ファイル: /{line}")
            for file in sorted(files):
                name = os.path.basename(file)
                print(f"パッケージ: {name}")
            print("")

def print_potential_duplicates(filter_archive=None):
    print("重複の恐れがあるライブラリ (.so):")
    for base_name, file_dict in potential_duplicates.items():
        if len(file_dict) > 1:
            if filter_archive and not any(f"PACKAGE:{filter_archive}" in file for file in file_dict.keys()):
                continue
            print(f"ベース名: /{base_name}")
            for file_path, lines in file_dict.items():
                for line in lines:
                    name = os.path.basename(file_path)
                    print(f"エントリ: /{line} ({name})")
            print("")

# 結果を表示
if archive_file:
    if 'a' in options:
        print_duplicates(filter_archive=archive_file)
        print_potential_duplicates(filter_archive=archive_file)
    elif 'p' in options:
        print_potential_duplicates(filter_archive=archive_file)
    else:
        print_duplicates(filter_archive=archive_file)
else:
    if 'a' in options:
        print_duplicates()
        print_potential_duplicates()
    elif 'p' in options:
        print_potential_duplicates()
    else:
        print_duplicates()

