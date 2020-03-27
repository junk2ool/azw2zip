/*
  azw2zip v.0.3
    Copyright (C) 2020 junk2ool
*/

■概要
KindleUnpackとDeDRM、DumpAZW6を改造してKindleの電子書籍(azw/azw3(あればresも))を画像のみの無圧縮zipかepubに変換するようにしたもの。
azwはWindowsならキーファイル(k4i)がなければ作り、変換します。(多分Macもだけど環境がないので未確認)
Linux(WSLも)では各自キーファイル(k4i)を別途用意してこれと同じディレクトリにおいてください。
Python 2.7(+pycrypto)が動く環境が必要です。
Kindleは1.24以前のものをインストールした環境でないとダメです。(DeDRMの仕様)

■開発環境
Windows 10とWSL(Ubuntu 18.4 LTS)のPython2.7、Kindle 1.24で開発＆動作確認を行っています。

■使用方法
各々の環境にPython 2.7(+pycrypto)を入れてazw2zip.pyに引数を渡して実行してください。
引数は、
azw2zip [-z] [-e] [-f] [-t] [-c] [-d] <azw_indir> [outdir]

 -z : zipを出力(出力形式省略時のデフォルト)
 -e : epubを出力
 -f : Imagesディレクトリを出力
 -t : ファイル名の作品名にUpdated_Titleを使用する(calibreと同じ形式)
 -c : zipでの出力時に圧縮をする
 -d : デバッグモード(各ツールの標準出力表示＆作業ディレクトリ消さない)
 azw_indir : 変換する書籍のディレクトリ(再帰的に読み込みます)
             (My Kindle Contentディレクトリを指定するとすべての書籍が変換されます)
 outdir : 出力先ディレクトリ(省略時はazw2zipと同じディレクトリ)

★注意★
-dを付けてazw_indirにMy Kindle Contentを指定するとすべての書籍を変換し、
すべての作業ファイルが残るのでストレージの空き容量に注意ください。 

・Windowsで毎回コマンドラインはめんどくさい人
Pythonの環境を整えてからazw2zip.vbsにpython.exeのパスを設定して、
変換したい書籍のディレクトリをazw2zip.vbsにD&Dするとこれと同じディレクトリにzipが作成されます。

■変更点
全般的にPython3への対応。

DeDRM - DeDRM_Plugin
・出力ファイル名を_nodrmを付けただけのものに変更。(k4mobidedrm.py)
・©のprintがWindows環境ではエラーになるので(C)に変更。(mobidedrm.py)
・python-lzmaを入れなくても大丈夫なように変更(多分)。(ion.py)
・S-JISに存在しないUnicode文字の表示がWindows環境でエラーが出ないように対策。(k4mobidedrm.py)

DumpAZW6
・外部から呼べるように関数を追加。(DumpAZW6_v01.py)
・受け付ける拡張子にresを追加。(DumpAZW6_v01.py)
・出力先を指定できるように変更。(DumpAZW6_v01.py)
・出力される画像のファイル名をHDimage->imageに変更。(DumpAZW6_v01.py)
・出力されるJPEG画像の拡張子をjpeg->jpgに変更。(DumpAZW6_v01.py)

KindleUnpack - KindleUnpack/lib
・外部から呼べるように関数を追加。(kindleunpack.py)
・出力されるJPEG画像の拡張子をjpeg->jpgに変更。(kindleunpack.py、mobi_cover.py)
・出力される画像の連番を00001からに変更。(kindleunpack.py)
・zipでも出力できるように追加。(kindleunpack.py、unpack_structure.py)
・epubでも出力できるように追加。(kindleunpack.py、unpack_structure.py)
・Imagesディレクトリを出力できるように追加。(kindleunpack.py、unpack_structure.py)
・DumpAZW6で出力したHD画像を取り込むように追加。(unpack_structure.py)
・S-JISに存在しないUnicode文字の表示がWindows環境でエラーが出ないように対策。(mobi_header.py)

■その他
出力されるファル名は、
[作者名] 作品名(.zip/.epub)
になります。
作者名は複数作者の場合 & で繋げるようになっています。
作品名はTitleを使用します。
-t オプションでUpdated_Titleを使うようになります。(calibreと同じ形式)
作者名、作品名をファイル名にする際のダメ文字は全角化するようにしています。(/を／等)

出力ファイル名を変えたければ、
KindleUnpack/lib/kindleunpack.py
の641行からの部分を変更してください。

■使用したもの等
DeDRM_tools 6.7.0
https://github.com/apprenticeharper/DeDRM_tools
のDeDRM_Plugin

DumpAZW6_v01.py
https://gist.github.com/fireattack/99b7d9f6b2896cfa33944555d9e2a158

KindleUnpack 0.82
https://github.com/kevinhendricks/KindleUnpack

作者名、作品名をファイル名にする際のダメ文字の置き換えには
https://fgshun.hatenablog.com/entry/20100213/1266032982
のsafefilenameを使用してダメ文字の全角化をするようにしています。(/を／等)

http://rio2016.5ch.net/test/read.cgi/ebooks/1526467330/395
の>>395さんの修正も取り込んでいます。

■ライセンス
GNU General Public License v3.0

■履歴
2020/03/xx v.0.3
・Python3での実行に対応。
・-zでzipを出力できるように追加。
・-fでImagesディレクトリを出力できるように追加。
・-eのepub出力をzip出力と排他的にならないように変更。
・-cでzip出力時に圧縮出来るように追加。
・html.entitiesがimport出来ずエラーになるのを修正。

2020/03/25 v.0.2
・S-JISに存在しないUnicode文字が作者名/作品名に含まれていた場合、出力ファイル名が数値文字参照になっていたのを修正。
・-dオプションを付けた場合、Windows環境で上記の時エラーになっていたのを対策。
・-dオプションを付けた場合、キーファイル(k4i)が作成できずエラーになっていたのを修正。

2020/03/23 v.0.1
・なんとなく形になったので公開
