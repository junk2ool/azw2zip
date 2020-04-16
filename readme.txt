/*
  azw2zip v.0.3
    Copyright (C) 2020 junk2ool
*/

■概要
KindleUnpackとDeDRM、DumpAZW6を改造してKindleの電子書籍(azw/azw3(あればresも))を画像のみの無圧縮zipかepubに変換するようにしたもの。
azwはWindowsならキーファイル(k4i)がなければ作り、変換します。(多分Macもだけど環境がないので未確認)
Linux(WSLも)では各自キーファイル(k4i)を別途用意してこれと同じディレクトリにおいてください。
Python 2.7かPython 3.8にpycryptoを入れたものが動く環境が必要です。
Kindleは1.24以前のものをインストールした環境でないとダメです。(DeDRMの仕様)

■開発環境
・Kindle 1.24
・Python 2.7.17 & Python 3.8.2
  ・Windows10
  ・WSL + Ubuntu 18.4 LTS
で開発＆動作確認を行っています。

■使用方法
各々の環境にPython 2.7かPython 3.8にpycryptoを入れてazw2zip.pyに引数を渡して実行してください。
引数は、
azw2zip [-zeftcod] <azw_indir> [outdir]

 -z : zipを出力(出力形式省略時のデフォルト)
 -e : epubを出力
 -f : 画像ファイルをディレクトリに出力
 -p : pdfを出力(PrintReplica書籍の場合のみ。作品名・作者名が正常でないものはamazon.co.jpより取得します)
 -t : ファイル名の作品名にUpdated_Titleを使用する(kindleと同じ作品名)
 -s : 作者名を昇順でソートする
 -c : zipでの出力時に圧縮をする
 -o : 出力時に上書きをする(デフォルトは上書きしない)
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

■ファイル名
出力されるファル名は、
[作者名] 作品名(.zip/.epub)
になります。
作者名は複数作者の場合 & で繋げるようになっています。(設定ファイルにて変更可能)
作者名が5名を超える場合、作者名(authors)を5名を超えたものは外n名となります。(設定ファイルにて変更可能)
作品名はTitleを使用します。
-t オプションでUpdated_Titleを使うようになります。(kindleと同じ作品名)
作者名、作品名をファイル名にする際のダメ文字は全角化するようにしています。(/を／等)

■設定ファイル
azw2zip.sample.jsonを参考にazw2zip.jsonにリネームするなりして使用してください。
引数を省略した場合のデフォルト値を設定できます。
出力ファイル名及びディレクトリによる振り分けは正規表現で設定することで変更可能です。
キーと値は、
author        作者名個別にマッチする正規表現。
authors       作者名を & で繋げたものにマッチする正規表現。
title         作品名にマッチする正規表現。
              グループ設定が可能で、(title)(series_index)(sub_title)の順で変数に値を代入できます。
series        シリーズ名。任意。変数が使えます。
series_index  巻数。任意。変数が使えます。
              titleキーの正規表現のグループで取るようにしていれば不要。全角数字は半角にします。
publisher     出版社。任意。変数が使えます。
directory     出力先。任意。変数が使えます。
sub_title     任意。変数が使えます。titleキーの正規表現のグループで取るようにした場合にも値が入ります。
template      リネーム書式。clibreのディスクに保存のテンプレートと同じで変数が使えます。
              ただし対応している変数は今の所上記の8つだけです。

ZENtoHAN      全角英数字記号を半角にします。任意。
pass          正規表現での置き換え等のみをして、templateでのリネームは行わず次の設定に回します。任意。
先頭から評価するので、ゆるい条件は最後の方に書いてください。

author変数は{author[0]}で1番目の作者名が取れます。

authorとauthors、titleは値をリスト化することで正規表現での置き換えが出来ます。
例:作者名の姓 名を姓名に
"author": [ "(.+)\\s+(.+)", "\\1\\2" ],

series、publisher、sub_titleも値をリスト化することで正規表現での置き換えが出来ます。
例:作品名の 雑誌名 2020年1号～ を雑誌名だけにしてseriesに設定。
"series": [ "(.+?)\\s+\\d{4}.+", "\\1", "{title}" ],
3つ目の値は省略可能で、省略した場合"{title}"と同等です。

azw2zip_config.pyで実装してます。

■変更点
全般的にPython3への対応。

DeDRM - DeDRM_Plugin
・出力ファイル名を_nodrmを付けただけのものに変更。(k4mobidedrm.py)
・©のprintがWindows環境ではエラーになるので(C)に変更。(mobidedrm.py)
・python-lzmaを入れなくても大丈夫なように変更。(ion.py)
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

■py2exeでのexe化
azw2zip/*.py
azw2zip/DeDRM_Plugin/*.py (__init__.py除く)
azw2zip/KindleUnpack/lib/*.py (__init__.py除く)
上記の*.pyを同じディレクトリに入れる。
python setup.py py2exe
を実行する。

■ToDo
・DeDRMのPython3対応は適当なので漏れがありそう。
・zip化の脱DeDRM+KindleUnpack。

■ライセンス
GNU General Public License v3.0

■履歴
2020/04/16 v.0.3
・Python3での実行に対応。
・-zでzipを出力できるように追加。
・-fで画像ファイルをディレクトリに出力出来るように追加。
・-pでpdfを出力できるように追加。(PrintReplica書籍の場合のみ。作品名・作者名が正常でないものはamazon.co.jpより取得します)
・-eのepub出力をzip出力と排他的にならないように変更。
・-sで作者名(authors)を昇順でソート出来るように追加。
・-cでzip出力時に圧縮出来るように追加。
・-oで出力時に上書きをするように追加。(デフォルトは上書きしない)
・azw2zip.jsonによるデフォルト値設定機能を追加。
・azw2zip.jsonによる出力ファイルのリネーム＆振り分け機能を追加。
・作者名が5名を超える場合、作者名(authors)を5名を超えたものは外n名とするように変更。(設定ファイルにて変更可能)
・作業ディレクトリ名を少し変更。
・py2exeでのexe化に対応。
・html.entitiesがimport出来ずエラーになるのを修正。
・ファイル名の一部文字がHTMLエスケープされていたのを修正。
・nav.xhtmlに存在しない表紙が登録され表紙が二重になってしまうことがあったのを修正。
・PrintReplica形式の書籍の変換でエラーになっていたのを修正。

2020/03/25 v.0.2
・S-JISに存在しないUnicode文字が作者名/作品名に含まれていた場合、出力ファイル名が数値文字参照になっていたのを修正。
・-dオプションを付けた場合、Windows環境で上記の時エラーになっていたのを対策。
・-dオプションを付けた場合、キーファイル(k4i)が作成できずエラーになっていたのを修正。

2020/03/23 v.0.1
・なんとなく形になったので公開
