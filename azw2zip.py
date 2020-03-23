#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os, os.path, getopt
import sys, os
import codecs
import contextlib
import glob
import shutil
import random
import string

__license__ = 'GPL v3'
__version__ = u"0.1"

sys.path.append(os.path.join(sys.path[0], "DeDRM_Plugin"))
sys.path.append(os.path.join(sys.path[0], 'KindleUnpack', 'lib'))

@contextlib.contextmanager
def redirect_stdout(target):
    original = sys.stdout
    sys.stdout = target
    yield
    sys.stdout = original

from argv_utils import add_cp65001_codec, set_utf8_default_encoding, unicode_argv
add_cp65001_codec()
set_utf8_default_encoding()

import DumpAZW6_v01
import kindleunpack
import kindleunpack.unipath

with redirect_stdout(open(os.devnull, 'w')):
    # AlfCrypto読み込み時の標準出力抑制
    import kindlekey
    from scriptinterface import decryptepub, decryptpdb, decryptpdf, decryptk4mobi

def usage(progname):
    print(u"Description:")
    print(u"  azw to zip or EPUB file.")
    print(u"  ")
    print(u"Usage:")
    print(u"  {} [-t] [-d] <azw_indir> [outdir]".format(progname))
    print(u"  ")
    print(u"Options:")
    print(u"  -t       ファイル名の作品名をUpdated_Titleを使用するように(calibreと同じ)")
    print(u"  -e       zipではなくepubを出力するように")
    print(u"  -d       デバッグモード(標準ログ表示＆作業ディレクトリ消さない)")

def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        # yield root
        for file in files:
            yield os.path.join(root, file)

def main(argv=unicode_argv()):
    print(u"azw2zip v.{0:s}\nCopyright (C) 2020 junk2ool".format(__version__))
    print(u"")

    progname = os.path.basename(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "ted")
    except getopt.GetoptError as err:
        print(str(err))
        usage(progname)
        sys.exit(2)

    if len(args) < 1:
        usage(progname)
        sys.exit(2)


    # オプション解析
    debug_mode = False
    updated_title = False
    output_epub = False
    for o, a in opts:
        if o == "-t":
            updated_title = True
        if o == "-e":
            output_epub = True
        if o == "-d":
            debug_mode = True

    # k4i ディレクトリはスクリプトのディレクトリ
    k4i_dir = os.path.dirname(os.path.abspath(__file__))
    print(u"k4iディレクトリ: {}".format(k4i_dir))
    k4i_files = glob.glob(os.path.join(k4i_dir, '*.k4i'))
    if not len(k4i_files):
        # k4iがなければ作成
        if not sys.platform.startswith('win') and not sys.platform.startswith('darwin'):
            # k4iはWindowsかMacでしか作成できない
            print(u"エラー : k4iファイルが見つかりません: {}".format(k4i_dir))
            exit(1)
        
        print(u"k4i作成: 開始: {}".format(k4i_dir))
        if debug_mode:
            kindlekey.make_kindlekey(k4i_dir)
        else:
            with redirect_stdout(open(os.devnull, 'w')):
                kindlekey.getkey(k4i_dir)
        k4i_files = glob.glob(os.path.join(k4i_dir, '*.k4i'))
        print(u"k4i作成: 完了: {}".format(k4i_files[0]))
    
    # 処理ディレクトリ
    in_dir = args[0]
    if not os.path.isabs(in_dir):
        in_dir = os.path.abspath(in_dir)
    if not in_dir:
        in_dir = os.getcwd()
    in_dir = os.path.realpath(os.path.normpath(in_dir))
    if (os.path.isfile(in_dir)):
        in_dir = os.path.dirname(in_dir)
    print(u"変換ディレクトリ: {}".format(in_dir))

    # 出力ディレクトリ作成
    out_dir = ""
    if len(args) > 1:
        out_dir = args[1]
        if not os.path.isabs(out_dir):
           out_dir = os.path.abspath(out_dir)
    if not out_dir:
        out_dir = os.getcwd()
    out_dir = os.path.realpath(os.path.normpath(out_dir))

    print(u"出力ディレクトリ: {}".format(out_dir))
    if not kindleunpack.unipath.exists(out_dir):
        kindleunpack.unipath.mkdir(out_dir)
        print(u"出力ディレクトリ: 作成: {}".format(out_dir))

    # 処理ディレクトリのファイルを再帰走査
    for azw_path in find_all_files(in_dir):
        # ファイルでなければスキップ
        if not os.path.isfile(azw_path):
            continue
        # .azwファイルでなければスキップ
        fext = os.path.splitext(azw_path)[1].upper()
        if fext not in ['.AZW', '.AZW3']:
            continue

        print("")
        azw_dir = os.path.dirname(azw_path)
        print(u"変換開始: {}".format(azw_dir))

        # 作業ディレクトリ作成
        # ランダムな8文字のディレクトリ名
        source = string.ascii_letters + string.digits
        random_str = ''.join([random.choice(source) for _ in range(8)])
        temp_dir = os.path.join(out_dir, random_str)
        book_fname = os.path.basename(os.path.dirname(azw_path))
        #temp_dir = os.path.join(out_dir, book_fname)
        print(u" 作業ディレクトリ: 作成: {}".format(temp_dir))
        if not kindleunpack.unipath.exists(temp_dir):
            kindleunpack.unipath.mkdir(temp_dir)

        # HD画像(resファイル)があれば展開
        res_files = glob.glob(os.path.join(os.path.dirname(azw_path), '*.res'))
        for res_path in res_files:
            print(u"  HD画像展開: 開始: {}".format(res_path))

            if debug_mode:
                DumpAZW6_v01.DumpAZW6(res_path, temp_dir)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    DumpAZW6_v01.DumpAZW6(res_path, temp_dir)

            print(u"  HD画像展開: 完了: {}".format(os.path.join(temp_dir, 'azw6_images')))

        # azwならDRM解除
        DeDRM_path = ""
        if fext in ['.AZW']:
            print(u"  DRM解除: 開始: {}".format(azw_path))

            if debug_mode:
                decryptk4mobi(azw_path, temp_dir, k4i_dir)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    decryptk4mobi(azw_path, temp_dir, k4i_dir)

            DeDRM_files = glob.glob(os.path.join(temp_dir, book_fname + '*.azw3'))
            if len(DeDRM_files) > 0:
                DeDRM_path = DeDRM_files[0]
                print(u"  DRM解除: 完了: {}".format(DeDRM_path))
            else:
                print(u"  DRM解除: 失敗:")
        elif fext in ['.AZW3']:
            DeDRM_path = azw_path

        if DeDRM_path and kindleunpack.unipath.exists(DeDRM_path):
            # zip/EPUB作成
            output_format = "zip"
            if output_epub:
                output_format = "epub"
            print(u"  {}変換: 開始: {}".format(output_format, DeDRM_path))

            #unpack_dir = os.path.join(temp_dir, os.path.splitext(os.path.basename(DeDRM_path))[0])
            unpack_dir = temp_dir
            if debug_mode:
                kindleunpack.kindleunpack(DeDRM_path, unpack_dir, updated_title, output_epub)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    kindleunpack.kindleunpack(DeDRM_path, unpack_dir, updated_title, output_epub)

            # 作成したzip/EPUBのファイル名を取得
            fname_path = os.path.join(temp_dir, "fname.txt")
            if kindleunpack.unipath.exists(fname_path):
                fname_file = codecs.open(fname_path, 'r', 'utf-8')
                fname_txt = fname_file.readline()
                print(u"  {}変換: 完了: {}".format(output_format, os.path.join(out_dir, fname_txt.rstrip())))
                fname_file.close()
            else:
                print(u"  {}変換: 失敗:".format(output_format))
        else:
            print(u"  DRM解除: 失敗:")

        if not debug_mode:
            shutil.rmtree(temp_dir)
            print(u" 作業ディレクトリ: 削除: {}".format(temp_dir))

        print(u"変換完了: {}".format(azw_dir))
    
    return 0

if __name__ == '__main__':
	sys.exit(main())
