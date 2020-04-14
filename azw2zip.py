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
__version__ = u"0.3"

sys.path.append(os.path.join(sys.path[0], "DeDRM_Plugin"))
sys.path.append(os.path.join(sys.path[0], 'KindleUnpack', 'lib'))

@contextlib.contextmanager
def redirect_stdout(target):
    original = sys.stdout
    sys.stdout = target
    yield
    sys.stdout = original

from compatibility_utils import add_cp65001_codec, unicode_argv
from argv_utils import  set_utf8_default_encoding
add_cp65001_codec()
set_utf8_default_encoding()

import DumpAZW6_v01
import kindleunpack
import unipath

from azw2zip_config import azw2zipConfig
from azw2zip_nodedrm import azw2zip
from azw2zip_nodedrm import azw2zipException

with redirect_stdout(open(os.devnull, 'w')):
    # AlfCrypto読み込み時の標準出力抑制
    import kindlekey
    from scriptinterface import decryptepub, decryptpdb, decryptpdf, decryptk4mobi

def usage(progname):
    print(u"Description:")
    print(u"  azw to zip or EPUB file.")
    print(u"  ")
    print(u"Usage:")
    print(u"  {} [-zeftscod] <azw_indir> [outdir]".format(progname))
    print(u"  ")
    print(u"Options:")
    print(u"  -z        zipを出力(出力形式省略時のデフォルト)")
    print(u"  -e        epubを出力")
    print(u"  -f        画像ファイルをディレクトリに出力")
    print(u"  -p        pdfを出力(PrintReplica書籍の場合のみ)")
    print(u"  -t        ファイル名の作品名にUpdated_Titleを使用する(Kindleと同じ作品名)")
    print(u"  -s        作者名を昇順でソートする")
    print(u"  -c        zipでの出力時に圧縮をする")
    print(u"  -o        出力時に上書きをする(デフォルトは上書きしない)")
    print(u"  -d        デバッグモード(各ツールの標準出力表示＆作業ディレクトリ消さない)")
    print(u"  azw_indir 変換する書籍のディレクトリ(再帰的に読み込みます)")
    print(u"  outdir    出力先ディレクトリ(省略時は{}と同じディレクトリ)".format(progname))

def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        # yield root
        for file in files:
            yield os.path.join(root, file)

def main(argv=unicode_argv()):
    progname = os.path.splitext(os.path.basename(argv[0]))[0]
    azw2zip_dir = os.path.dirname(os.path.abspath(argv[0]))

    print(u"{0:} v.{1:s}\nCopyright (C) 2020 junk2ool".format(progname, __version__))
    print(u"")

    try:
        opts, args = getopt.getopt(argv[1:], "zefptscomd")
    except getopt.GetoptError as err:
        print(str(err))
        usage(progname)
        sys.exit(2)

    if len(args) < 1:
        usage(progname)
        sys.exit(2)

    cfg = azw2zipConfig()
    cfg.load(os.path.join(azw2zip_dir, 'azw2zip.json'))

    updated_title = cfg.isUpdatedTitle()
    authors_sort = cfg.isAuthorsSort()
    compress_zip = cfg.isCompressZip()
    over_write = cfg.isOverWrite()
    output_thumb = cfg.isOutputThumb()
    output_zip = cfg.isOutputZip()
    output_epub = cfg.isOutputEpub()
    output_images = cfg.isOutputImages()
    output_pdf = cfg.isOutputPdf()
    debug_mode = cfg.isDebugMode()

    # オプション解析
    for o, a in opts:
        if o == "-t":
            updated_title = True
        if o == "-s":
            authors_sort = True
        if o == "-c":
            compress_zip = True
        if o == "-o":
            over_write = True
        if o == "-m":
            output_thumb = True
        if o == "-z":
            output_zip = True
        if o == "-e":
            output_epub = True
        if o == "-f":
            output_images = True
        if o == "-p":
            output_pdf = True
        if o == "-d":
            debug_mode = True
    if not output_zip and not output_epub and not output_images and not output_pdf:
        output_zip = True
    cfg.setOptions(updated_title, authors_sort, compress_zip, over_write, output_thumb, debug_mode)
    cfg.setOutputFormats(output_zip, output_epub, output_images, output_pdf)

    # k4i ディレクトリはスクリプトのディレクトリ
    k4i_dir = cfg.getk4iDirectory()
    if not k4i_dir:
        k4i_dir = azw2zip_dir
    print(u"k4iディレクトリ: {}".format(k4i_dir))
    cfg.setk4iDirectory(k4i_dir)
    k4i_files = glob.glob(os.path.join(k4i_dir, '*.k4i'))
    if not len(k4i_files):
        # k4iがなければ作成
        if not sys.platform.startswith('win') and not sys.platform.startswith('darwin'):
            # k4iはWindowsかMacでしか作成できない
            print(u"エラー : k4iファイルが見つかりません: {}".format(k4i_dir))
            exit(1)
        
        print(u"k4i作成: 開始: {}".format(k4i_dir))
        if debug_mode:
            kindlekey.getkey(k4i_dir)
        else:
            with redirect_stdout(open(os.devnull, 'w')):
                kindlekey.getkey(k4i_dir)
        k4i_files = glob.glob(os.path.join(k4i_dir, '*.k4i'))
        print(u"k4i作成: 完了: {}".format(k4i_files[0]))
    else:
        for k4i_fpath in k4i_files:
            print(u"k4i: {}".format(k4i_fpath))
    
    # 変換ディレクトリ
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
    out_dir = cfg.getOutputDirectory()
    if len(args) > 1:
        out_dir = args[1]
        if not os.path.isabs(out_dir):
           out_dir = os.path.abspath(out_dir)
    if not out_dir:
        out_dir = azw2zip_dir #os.getcwd()
    out_dir = os.path.realpath(os.path.normpath(out_dir))
    cfg.setOutputDirectory(out_dir)

    print(u"出力ディレクトリ: {}".format(out_dir))
    if not unipath.exists(out_dir):
        unipath.mkdir(out_dir)
        print(u"出力ディレクトリ: 作成: {}".format(out_dir))

    output_zip_org = output_zip
    output_epub_org = output_epub
    output_images_org = output_images
    output_pdf_org = output_pdf

    # 処理ディレクトリのファイルを再帰走査
    for azw_fpath in find_all_files(in_dir):
        # ファイルでなければスキップ
        if not os.path.isfile(azw_fpath):
            continue
        # .azwファイルでなければスキップ
        fext = os.path.splitext(azw_fpath)[1].upper()
        if fext not in ['.AZW', '.AZW3']:
            continue

        output_zip = output_zip_org
        output_epub = output_epub_org
        output_images = output_images_org
        output_pdf = output_pdf_org
        
        output_format = [
            [output_zip, u"zip", u".zip"],
            [output_epub, u"epub", u".epub"],
            [output_images, u"Images", u""],
            [output_pdf, u"pdf", u".*.pdf"],
        ]

        print("")
        azw_dir = os.path.dirname(azw_fpath)
        print(u"変換開始: {}".format(azw_dir))

        # 上書きチェック
        a2z = azw2zip()
        over_write_flag = over_write
        try:
            if a2z.load(azw_fpath, '', debug_mode) != 0:
                over_write_flag = True
        except azw2zipException as e:
            print(str(e))
            over_write_flag = True

        cfg.setPrintReplica(a2z.is_print_replica())

        if not over_write_flag:
            fname_txt = cfg.makeOutputFileName(a2z.get_meta_data())
            for format in output_format:
                if format[0]:
                    output_fpath = os.path.join(out_dir, fname_txt + format[2])
                    output_files = glob.glob(output_fpath.replace('[', '[[]'))
                    if (len(output_files)):
                        format[0] = False
                        try:
                            print(u" {}変換: パス: {}".format(format[1], output_files[0]))
                        except UnicodeEncodeError:
                            print(u" {}変換: パス: {}".format(format[1], output_files[0].encode('cp932', 'replace').decode('cp932')))
                    else:
                        over_write_flag = True

        if not over_write_flag:
            # すべてパス
            print(u"変換完了: {}".format(azw_dir))
            continue

        cfg.setOutputFormats(output_zip, output_epub, output_images, output_pdf)

        # 作業ディレクトリ作成
        # ランダムな8文字のディレクトリ名
        source = string.ascii_letters + string.digits
        random_str = ''.join([random.choice(source) for _ in range(8)])
        temp_dir = os.path.join(out_dir, "Temp_" + random_str)
        book_fname = os.path.basename(os.path.dirname(azw_fpath))
        #temp_dir = os.path.join(out_dir, book_fname)
        print(u" 作業ディレクトリ: 作成: {}".format(temp_dir))
        if not unipath.exists(temp_dir):
            unipath.mkdir(temp_dir)

        cfg.setTempDirectory(temp_dir)

        # HD画像(resファイル)があれば展開
        res_files = glob.glob(os.path.join(os.path.dirname(azw_fpath), '*.res'))
        for res_fpath in res_files:
            print(u"  HD画像展開: 開始: {}".format(res_fpath))

            if debug_mode:
                DumpAZW6_v01.DumpAZW6(res_fpath, temp_dir)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    DumpAZW6_v01.DumpAZW6(res_fpath, temp_dir)

            print(u"  HD画像展開: 完了: {}".format(os.path.join(temp_dir, 'azw6_images')))

        # azwならDRM解除
        DeDRM_path = ""
        if fext in ['.AZW']:
            print(u"  DRM解除: 開始: {}".format(azw_fpath))

            if debug_mode:
                decryptk4mobi(azw_fpath, temp_dir, k4i_dir)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    decryptk4mobi(azw_fpath, temp_dir, k4i_dir)

            DeDRM_files = glob.glob(os.path.join(temp_dir, book_fname + '*.azw?'))
            if len(DeDRM_files) > 0:
                DeDRM_path = DeDRM_files[0]
                print(u"  DRM解除: 完了: {}".format(DeDRM_path))
            else:
                print(u"  DRM解除: 失敗:")
        elif fext in ['.AZW3']:
            DeDRM_path = azw_fpath

        if DeDRM_path and unipath.exists(DeDRM_path):
            # 書籍変換
            print(u"  書籍変換: 開始: {}".format(DeDRM_path))

            #unpack_dir = os.path.join(temp_dir, os.path.splitext(os.path.basename(DeDRM_path))[0])
            unpack_dir = temp_dir
            if debug_mode:
                kindleunpack.kindleunpack(DeDRM_path, unpack_dir, cfg)
            else:
                with redirect_stdout(open(os.devnull, 'w')):
                    kindleunpack.kindleunpack(DeDRM_path, unpack_dir, cfg)

            # 作成したファイル名を取得
            fname_path = os.path.join(temp_dir, "fname.txt")
            if unipath.exists(fname_path):
                fname_file = codecs.open(fname_path, 'r', 'utf-8')
                fname_txt = fname_file.readline().rstrip()
                fname_file.close()

                for format in output_format:
                    if format[0]:
                        output_fpath = os.path.join(out_dir, fname_txt + format[2])
                        output_files = glob.glob(output_fpath.replace('[', '[[]'))
                        if (len(output_files)):
                            try:
                                print(u"  {}変換: 完了: {}".format(format[1], output_files[0]))
                            except UnicodeEncodeError:
                                print(u"  {}変換: 完了: {}".format(format[1], output_files[0].encode('cp932', 'replace').decode('cp932')))
            else:
                print(u"  書籍変換: 失敗:")
        else:
            print(u"  DRM解除: 失敗:")

        if not debug_mode:
            shutil.rmtree(temp_dir)
            print(u" 作業ディレクトリ: 削除: {}".format(temp_dir))

        print(u"変換完了: {}".format(azw_dir))

    return 0

if __name__ == '__main__':
	sys.exit(main())
