# 概要
Plamo Linuxにインストールされているパッケージに重複しているファイルが含まれるか調べる。

# 使用方法
## インストールされているパッケージ群から重複しているファイルを含むパッケージを調べる
```
find_duplicate.py
```

## 2つのパッケージから重複しているファイルを調べる
```
find_duplicate.py samba tdb
```

## 重複する可能性のあるライブラリを含むパッケージを調べる
例えば以下のようなライブラリを含むパッケージを調べる。<br>
エントリ: /usr/lib/libicudata.so.74 (icu)<br>
エントリ: /usr/lib/libicudata.so.70 (icu70)<br>
```
find_duplicate.py -p
```

## 重複しているファイルを含むパッケージと重複する可能性のあるライブラリを含むパッケージを同時に調べる
```
find_duplicate.py -a
```

## 調べるパッケージから除外する
$HOME/.find_duplicate.confに次のように記述する
```
BLOCK=gcc libgcc Python XPython lib32_*
```
