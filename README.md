# azw2zip

KindleUnpackとDeDRM、DumpAZW6を改造してKindleの電子書籍(azw/azw3(あればresも))を画像のみの無圧縮zipかepubに変換するようにしたもの。  
azwはWindowsならキーファイル(k4i)がなければ作り、変換します。(多分Macもだけど環境がないので未確認)  
Linux(WSLも)では各自キーファイル(k4i)を別途用意してこれと同じディレクトリにおいてください。  
Python 2.7かPython 3.8にpycryptoを入れたものが動く環境が必要です。  
Kindleは1.24以前のものをインストールした環境でないとダメです。(DeDRMの仕様)  

## Requirement
* Python 2.7 or 3.8
* pycrypto

## Usage
```
python azw2zip.py -z X:\My Kindle Content X:\Comic
```
詳しくはreadme.txtを参照。

## Development environment
 * Kindle 1.24
 * Python 2.7.17 & Python 3.8.2
   * Windows 10
   * Ubuntu 18.4 LTS(WSL)

## Note

### py2exe
p2exeをインストールする。  
 * azw2zip/\*.py  
 * azw2zip/DeDRM_Plugin/\*.py (\_\_init\_\_.py除く)  
 * azw2zip/KindleUnpack/lib/\*.py (\_\_init\_\_.py除く)  

上記の\*.pyを同じディレクトリに入れる。  
```
python setup.py py2exe  
```
を実行する。

## License
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.ja.html)

## Author
* junk2ool
* https://www.junk2ool.net/
* https://github.com/junk2ool/azw2zip

## References
* DeDRM_tools 6.7.0  
https://github.com/apprenticeharper/DeDRM_tools  
のDeDRM_Plugin

* DumpAZW6_v01.py  
https://gist.github.com/fireattack/99b7d9f6b2896cfa33944555d9e2a158

* KindleUnpack 0.82  
https://github.com/kevinhendricks/KindleUnpack

* 作者名、作品名をファイル名にする際のダメ文字の置き換えには  
https://fgshun.hatenablog.com/entry/20100213/1266032982  
のsafefilenameを使用してダメ文字の全角化をするようにしています。(/を／等)

* http://rio2016.5ch.net/test/read.cgi/ebooks/1526467330/  
の[>>395](http://rio2016.5ch.net/test/read.cgi/ebooks/1526467330/395)さんの修正も取り込んでいます。
