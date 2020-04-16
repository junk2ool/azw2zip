#!/usr/bin/env python
# coding: utf-8

import os
import sys
import codecs
import traceback

import json
from collections import OrderedDict
import pprint
import re

try:
    import urllib2 as ul
except ImportError:
    import urllib.request as ul

try:
    from urllib.parse import unquote, unquote_plus
except ImportError:
    from urllib import unquote, unquote_plus

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    from HTMLParser import HTMLParser
    _h = HTMLParser()
elif sys.version_info[1] < 4:
    import html.parser
    _h = html.parser.HTMLParser()
else:
    import html as _h

import safefilename as sfn

class azw2zipConfig:

    def __init__(self):
        self.filename = ''
        self.json = OrderedDict()

        self.updated_title = False
        self.compress_zip = False
        self.over_write = False
        self.output_thumb = False
        self.output_zip = False
        self.output_epub = False
        self.output_images = False
        self.output_pdf = False
        self.outdir = ''
        self.k4idir = ''
        self.tmpdir = ''
        self.authors_sep = u' & '
        self.authors_sort = False
        self.authors_others = u'外{}名'
        self.authors_others_threshold = 5
        self.cover_fname = u"cover{num1:0>5}.{ext}"
        self.image_fname = u"image{num1:0>5}.{ext}"
        self.thumb_fname = u"thumb{num1:0>5}.{ext}"
        #self.cover_fname = u'cover.{ext}'
        #self.image_fname = u'image{image_num1:0>3}.{ext}'
        #self.thumb_fname = u'thumbnail.{ext}'
        self.debug_mode = False
        #
        self.metadata = OrderedDict()
        self.print_replica = False

    def load(self, filename):
        self.filename = filename
        if not os.path.exists(self.filename):
            return 1

        with open(self.filename, 'rb') as f:
            self.json = json.load(f, object_pairs_hook=OrderedDict)

            if 'default' in self.json:
                for key_info in self.json['default']:
                    if 'updated_title' in key_info and key_info['updated_title']:
                        self.updated_title = True
                    if 'compress_zip' in key_info and key_info['compress_zip']:
                        self.compress_zip = True
                    if 'over_write' in key_info and key_info['over_write']:
                        self.over_write = True
                    if 'output_thumb' in key_info and key_info['output_thumb']:
                        self.output_thumb = True
                    if 'output_zip' in key_info and key_info['output_zip']:
                        self.output_zip = True
                    if 'output_epub' in key_info and key_info['output_epub']:
                        self.output_epub = True
                    if 'output_images' in key_info and key_info['output_images']:
                        self.output_images = True
                    if 'output_pdf' in key_info and key_info['output_pdf']:
                        self.output_pdf = True
                    if 'output_dir' in key_info:
                        self.outdir = key_info['output_dir']
                    if 'k4i_dir' in key_info:
                        self.k4idir = key_info['k4i_dir']
                    if 'authors_sep' in key_info:
                        self.authors_sep = key_info['authors_sep']
                    if 'authors_sort' in key_info and key_info['authors_sort']:
                        self.authors_sort = True
                    if 'authors_others' in key_info:
                        self.authors_others = key_info['authors_others']
                    if 'authors_others_threshold' in key_info:
                        self.authors_others_threshold = int(key_info['authors_others_threshold'])
                    if 'cover_fname' in key_info:
                        self.cover_fname = key_info['cover_fname']
                    if 'image_fname' in key_info:
                        self.image_fname = key_info['image_fname']
                    if 'thumb_fname' in key_info:
                        self.thumb_fname = key_info['thumb_fname']
                    if 'debug_mode' in key_info and key_info['debug_mode']:
                        self.debug_mode = True
        return 0

    def getJSON(self):
        return self.json

    def getk4iDirectory(self):
        return self.k4idir

    def setk4iDirectory(self, k4idir):
        self.k4idir = k4idir

    def isUpdatedTitle(self):
        return self.updated_title

    def isAuthorsSort(self):
        return self.authors_sort

    def isCompressZip(self):
        return self.compress_zip

    def isOverWrite(self):
        return self.over_write

    def isOutputThumb(self):
        return self.output_thumb

    def isOutputZip(self):
        return self.output_zip

    def isOutputEpub(self):
        return self.output_epub

    def isOutputImages(self):
        return self.output_images

    def isOutputPdf(self):
        return self.output_pdf

    def isDebugMode(self):
        return self.debug_mode

    def setPrintReplica(self, print_replica):
        self.print_replica = print_replica
        self.metadata.clear()

    def setOptions(self, updated_title, authors_sort, compress_zip, over_write, output_thumb, debug_mode):
        self.updated_title = updated_title
        self.authors_sort = authors_sort
        self.compress_zip = compress_zip
        self.over_write = over_write
        self.output_thumb = output_thumb
        self.debug_mode = debug_mode

    def setOutputFormats(self, output_zip, output_epub, output_images, output_pdf):
        self.output_zip = output_zip
        self.output_epub = output_epub
        self.output_images = output_images
        self.output_pdf = output_pdf

    def getOutputDirectory(self):
        return self.outdir

    def getCoverFilename(self):
        return self.cover_fname

    def getImageFilename(self):
        return self.image_fname

    def getThumbFilename(self):
        return self.thumb_fname

    def setOutputDirectory(self, outdir):
        self.outdir = outdir

    def setTempDirectory(self, tmpdir):
        self.tmpdir = tmpdir

    def getAmazonMetaData(self, asin):
        url = 'https://www.amazon.co.jp/dp/' + asin
        #print(url)
        request = ul.Request(url)
        request.add_header('User-agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36')
        response = ul.urlopen(request)

        html_data = response.read()
        if self.debug_mode and self.tmpdir and html_data:
            with open(os.path.join(self.tmpdir, asin + ".html"), "wb") as f:
                f.write(html_data)

        if response.getcode() != 200:
            return
        
        if type(html_data) is bytes:
            html_data = html_data.decode('utf-8')

        title_match = re.search(r'<span id=".*?roductTitle".+?>\s+(.+?)\s+?</span>', html_data)
        if (title_match):
            #print(title_match.group(1))
            del self.metadata['Title']
            del self.metadata['Updated_Title']
            self.metadata['Title'] = [title_match.group(1)]
            self.metadata['Updated_Title'] = [title_match.group(1)]

        author_match = re.search(r'field-author=(.+?)&amp;', html_data)
        if author_match:
            del self.metadata['Creator']
        for m in re.findall(r'field-author=(.+?)&amp;', html_data):
            #print(m)
            author = u''
            if PY2:
                author = unquote_plus(m.encode('ascii')).decode('utf-8')
            else:
                author = unquote_plus(m)
            #print(author)
            if 'Creator' not in self.metadata:
                self.metadata['Creator'] = [author]
            else:
                self.metadata['Creator'].append(author)

        publisher_match = re.search(u'<li><b>出版社:</b>\s+?(.+?)\s+?\(.+?\)</li>', html_data)
        if (publisher_match):
            #print(publisher_match.group(1))
            del self.metadata['Publisher']
            self.metadata['Publisher'] = [publisher_match.group(1)]

    def makeAuthors(self, author):
        #return self.author_seps.join(author)
        if self.authors_sort:
            author.sort()
        authors = u''
        for index in range(len(author)):
            if index != 0:
                authors += self.authors_sep
            if self.authors_others_threshold > 0 and index >= self.authors_others_threshold:
                authors += self.authors_others.format(len(author) - self.authors_others_threshold)
                break
            #authors += _h.unescape(unicode_str(author[index]))
            #authors += sfn.safefilename(_h.unescape(unicode_str(author[index])), table=sfn.table2)
            authors += author[index]
        return authors

    def makeOutputFileName(self, metadata):
        title = metadata.get('Title')[0]
        #
        if self.print_replica and title[:4] == u'tmp-' and metadata.get('ASIN')[0]:
            try:
                if not self.metadata.get('Title'):
                    self.metadata = metadata.copy()
                    self.getAmazonMetaData(self.metadata.get('ASIN')[0])
                metadata = self.metadata.copy()
                title = metadata.get('Title')[0]
                #print(metadata)
            except Exception as e:
                print(str(e))
                pass

        # Title
        if self.updated_title and 'Updated_Title' in metadata:
            title = metadata.get('Updated_Title')[0]
        title = _h.unescape(title)
        # Creator
        author = []
        for index in range(len(metadata.get('Creator'))):
            author.append(sfn.safefilename(_h.unescape(metadata.get('Creator')[index]), table=sfn.table2))
        #
        publisher = ''
        if 'Publisher' in metadata:
            publisher = metadata.get('Publisher')[0]
            publisher = sfn.safefilename(publisher, table=sfn.table2)
        #
        title = sfn.safefilename(title, table=sfn.table2)
        authors = self.makeAuthors(author)

        # 全角→半角用辞書
        ZEN2HAN_dict = dict((0xff00 + ch, 0x0020 + ch) for ch in range(0x5f))
        ZEN2HAN_dict[0x3000] = 0x0020

        # ファイル名作成 デフォルトは [authors] title
        outdir = ''
        series = ''
        series_index = '0'
        rename_template = u'[{authors}] {title}'
        org_title = title
        sub_title = ''

        # azw2zip.json のテンプレートを読み込んでリネーム
        if 'rename' in self.json:
            for rename_info in self.json['rename']:
                match_author = False
                match_title = False
                if 'author' in rename_info:
                    author_value = rename_info['author']
                    if type(author_value) is list:
                        for index in range(len(author)):
                            if (re.match(author_value[0], author[index])):
                                author[index] = re.sub(author_value[0], author_value[1], author[index])
                                authors = self.makeAuthors(author)
                                match_author = True
                    else:
                        for index in range(len(author)):
                            if (re.match(author_value, author[index])):
                                match_author = True
                                break
                if 'authors' in rename_info:
                    author_value = rename_info['authors']
                    if type(author_value) is list:
                        if (re.match(author_value[0], authors)):
                            authors = re.sub(author_value[0], author_value[1], authors)
                            match_author = True
                    else:
                        match_author = re.match(rename_info['authors'], authors)
                if 'title' in rename_info:
                    title_value = rename_info['title']
                    if type(title_value) is list:
                        if (re.match(title_value[0], title)):
                            title = re.sub(title_value[0], title_value[1], title)
                            match_title = True
                    else:
                        match_title = re.match(title_value, title)
                if match_author and match_title:
                    if len(match_title.groups()):
                        title = match_title.group(1)
                        if len(match_title.groups()) > 1:
                            series_index = match_title.group(2).translate(ZEN2HAN_dict)
                        if len(match_title.groups()) > 2:
                            sub_title = match_title.group(3)
                    if 'series' in rename_info:
                        series_value = rename_info['series']
                        if type(series_value) is list:
                            tmp_str = title
                            if len(series_value) > 2:
                                tmp_str = series_value[2].format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                            series = re.sub(series_value[0], series_value[1], tmp_str)
                        else:
                            series = series_value.format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                    if 'series_index' in rename_info:
                        match_series_index = re.match(rename_info['series_index'], org_title)
                        if match_series_index and len(match_series_index.groups()):
                            series_index = match_series_index.group(1).translate(ZEN2HAN_dict)
                    if 'sub_title' in rename_info:
                        sub_title_value = rename_info['sub_title']
                        if type(sub_title_value) is list:
                            tmp_str = title
                            if len(sub_title_value) > 2:
                                tmp_str = sub_title_value[2].format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                            sub_title = re.sub(sub_title_value[0], sub_title_value[1], tmp_str)
                        else:
                            sub_title = sub_title_value.format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                    if 'publisher' in rename_info:
                        publisher_value = rename_info['publisher']
                        if type(publisher_value) is list:
                            tmp_str = title
                            if len(publisher_value) > 2:
                                tmp_str = publisher_value[2].format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                            publisher = re.sub(publisher_value[0], publisher_value[1], tmp_str)
                        else:
                            publisher = publisher_value.format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                    # ZENtoHAN
                    if 'ZENtoHAN' in rename_info and rename_info['ZENtoHAN']:
                        for index in range(len(author)):
                            author[index] = sfn.safefilename(author[index].translate(ZEN2HAN_dict), table=sfn.table2)
                        if authors:
                            authors = sfn.safefilename(authors.translate(ZEN2HAN_dict), table=sfn.table2)
                        if title:
                            title = sfn.safefilename(title.translate(ZEN2HAN_dict), table=sfn.table2)
                        if sub_title:
                            sub_title = sfn.safefilename(sub_title.translate(ZEN2HAN_dict), table=sfn.table2)
                        if series:
                            series = sfn.safefilename(series.translate(ZEN2HAN_dict), table=sfn.table2)
                        if publisher:
                            publisher = sfn.safefilename(publisher.translate(ZEN2HAN_dict), table=sfn.table2)
                    #
                    if 'directory' in rename_info:
                        outdir = rename_info['directory'].format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)
                        if sys.platform.startswith('win'):
                            outdir = outdir.replace('/', os.sep)
                        else:
                            outdir = outdir.replace('\\', os.sep)
                    if 'template' in rename_info:
                        rename_template = rename_info['template']
                    #
                    if not 'pass' in rename_info or not rename_info['pass']:
                        break

        fname = rename_template.format(author=author, authors=authors, title=title, series=series, series_index=series_index, publisher=publisher, sub_title=sub_title, org_title = org_title)

        return os.path.join(outdir, fname)
