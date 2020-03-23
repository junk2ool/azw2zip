/*
  azw2zip v.0.1
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
azw2zip [-t] [-e] [-d] <azw_indir> [outdir]

 -t : ファイル名の作品名をUpdated_Titleを使用するように(calibreと同じ形式)
 -e : zipではなくepubを出力するように
 -d : デバッグモード(標準出力表示＆作業ファイルを消さない)
 azw_indir : My Kindle Content内の変換したい書籍のディレクトリ
             (ディレクトリを再帰的に読み込むのでMy Kindle Contentディレクトリを指定するとすべての書籍を変換出来ます)
 outdir : 出力先(省略するとこれと同じディレクトリ)

★注意★
-dを付けてazw_indirにMy Kindle Contentを指定するとすべての書籍を変換し、
すべての作業ファイルが残るのでストレージの空き容量に注意ください。 

・Windowsで毎回コマンドラインはめんどくさい人
Pythonの環境を整えてからazw2zip.vbsにpython.exeのパスを設定して、
変換したい書籍のディレクトリをazw2zip.vbsにD&Dするとこれと同じディレクトリにzipが作成されます。

■変更点
DeDRM
・出力ファイル名を_nodrmを付けただけのものに変更。(DeDRM_Plugin/k4mobidedrm.py)
・©のprintがWindows環境ではエラーになるので(C)に変更。(DeDRM_Plugin/mobidedrm.py)
・python-lzmaを入れなくても大丈夫なように変更(多分)。(DeDRM_Plugin/ion.py)

DumpAZW6
・外部から呼べるように関数を追加。(DumpAZW6_v01.py)
・受け付ける拡張子にresを追加。(DumpAZW6_v01.py)
・出力先を指定できるように変更。(DumpAZW6_v01.py)
・出力される画像のファイル名をHDimage->imageに変更。(DumpAZW6_v01.py)
・出力されるJPEG画像の拡張子をjpeg->jpgに変更。(DumpAZW6_v01.py)

KindleUnpack
・外部から呼べるように関数を追加。(KindleUnpack/lib/kindleunpack.py)
・出力されるJPEG画像の拡張子をjpeg->jpgに変更。(KindleUnpack/lib/kindleunpack.py、KindleUnpack/lib/mobi_cover.py)
・出力される画像の連番を00001からに変更。(KindleUnpack/lib/kindleunpack.py)
・zipでも出力できるように追加。(KindleUnpack/lib/kindleunpack.py、KindleUnpack/lib/unpack_structure.py)
・DumpAZW6で出力したHD画像を取り込むように追加。(KindleUnpack/lib/unpack_structure.py)

■その他
出力されるファル名は、
[作者名] 作品名.zip(.epub)
になります。
作者名は複数作者の場合 & で繋げるようになっています。
作品名はTitleを使用します。
-t オプションでUpdated_Titleを使うようになります。(calibreと同じ形式)
作者名、作品名をファイル名にする際のダメ文字は全角化するようにしています。(/を／等)

出力ファイル名を変えたければ、
KindleUnpack/lib/kindleunpack.py
の623行からの部分を変更してください。

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
2020/03/23 v.0.1
・なんとなく形になったので公開
