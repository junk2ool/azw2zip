#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import getopt
import struct
import glob

import shutil
import binascii
import zipfile
import imghdr
from collections import OrderedDict as dict_
from datetime import datetime as dt

__license__ = 'GPL v3'
__version__ = u"0.1"

from azw2zip_config import azw2zipConfig

JPEG_EXT = u'jpg'

class azw2zipException(Exception):
    pass

class azw_header:
    id_map_strings = {
        1 : 'Drm Server Id',
        2 : 'Drm Commerce Id',
        3 : 'Drm Ebookbase Book Id',
        4 : 'Drm Ebookbase Dep Id',
        100 : 'Creator',
        101 : 'Publisher',
        102 : 'Imprint',
        103 : 'Description',
        104 : 'ISBN',
        105 : 'Subject',
        106 : 'Published',
        107 : 'Review',
        108 : 'Contributor',
        109 : 'Rights',
        110 : 'SubjectCode',
        111 : 'Type',
        112 : 'Source',
        113 : 'ASIN',
        114 : 'versionNumber',
        117 : 'Adult',
        118 : 'Retail-Price',
        119 : 'Retail-Currency',
        120 : 'TSC',
        122 : 'fixed-layout',
        123 : 'book-type',
        124 : 'orientation-lock',
        126 : 'original-resolution',
        127 : 'zero-gutter',
        128 : 'zero-margin',
        129 : 'MetadataResourceURI',
        132 : 'RegionMagnification',
        150 : 'LendingEnabled',
        200 : 'DictShortName',
        501 : 'cdeType',
        502 : 'last_update_time',
        503 : 'Updated_Title',
        504 : 'CDEContentKey',
        505 : 'AmazonContentReference',
        506 : 'Title-Language',
        507 : 'Title-Display-Direction',
        508 : 'Title-Pronunciation',
        509 : 'Title-Collation',
        510 : 'Secondary-Title',
        511 : 'Secondary-Title-Language',
        512 : 'Secondary-Title-Direction',
        513 : 'Secondary-Title-Pronunciation',
        514 : 'Secondary-Title-Collation',
        515 : 'Author-Language',
        516 : 'Author-Display-Direction',
        517 : 'Author-Pronunciation',
        518 : 'Author-Collation',
        519 : 'Author-Type',
        520 : 'Publisher-Language',
        521 : 'Publisher-Display-Direction',
        522 : 'Publisher-Pronunciation',
        523 : 'Publisher-Collation',
        524 : 'Content-Language-Tag',
        525 : 'primary-writing-mode',
        526 : 'NCX-Ingested-By-Software',
        527 : 'page-progression-direction',
        528 : 'override-kindle-fonts',
        529 : 'Compression-Upgraded',
        530 : 'Soft-Hyphens-In-Content',
        531 : 'Dictionary_In_Langague',
        532 : 'Dictionary_Out_Language',
        533 : 'Font_Converted',
        534 : 'Amazon_Creator_Info',
        535 : 'Creator-Build-Tag',
        536 : 'HD-Media-Containers-Info',  # CONT_Header is 0, Ends with CONTAINER_BOUNDARY (or Asset_Type?)
        538 : 'Resource-Container-Fidelity',
        539 : 'HD-Container-Mimetype',
        540 : 'Sample-For_Special-Purpose',
        541 : 'Kindletool-Operation-Information',
        542 : 'Container_Id',
        543 : 'Asset-Type',  # FONT_CONTAINER, BW_CONTAINER, HD_CONTAINER
        544 : 'Unknown_544',
    }
    id_map_values = {
        115 : 'sample',
        116 : 'StartOffset',
        121 : 'Mobi8-Boundary-Section',
        125 : 'Embedded-Record-Count',
        130 : 'Offline-Sample',
        131 : 'Metadata-Record-Offset',
        201 : 'CoverOffset',
        202 : 'ThumbOffset',
        203 : 'HasFakeCover',
        204 : 'Creator-Software',
        205 : 'Creator-Major-Version',
        206 : 'Creator-Minor-Version',
        207 : 'Creator-Build-Number',
        401 : 'Clipping-Limit',
        402 : 'Publisher-Limit',
        404 : 'Text-to-Speech-Disabled',
        406 : 'Rental-Expiration-Time',
    }

    def __init__(self, fpath, debug):
        self.fpath = fpath
        self.f = None
        self.debug = debug

        self.type = b''
        self.sec_offset = 0
        self.sec_count = 0
        self.header = b''
        self.header_offset = 0
        self.header_size = 0
        self.mobi_header_offset = 0x10

        self.version = 0
        self.codepage = 1252
        self.codec = 'windows-1252'
        self.first_resc_offset = 0
        #
        self.exth = b''
        self.exth_offset = 0
        self.exth_size = 0
        #
        self.meta_data = dict_()
        self.image_data = dict_()

    def __del__(self):
        self.close()

    def set_header(self, sec_offset, header, header_size, header_offset):
        self.sec_offset = sec_offset
        self.header = header
        self.header_offset = header_offset
        self.header_size = header_size

        header_type = header[:4]
        if header_type == b'\x44\x48\x00\x00' or header_type == b'\x00\x01\x00\x00' or header_type == b'\x00\x02\x00\x00':
            self.type = 'MOBI'
            self.parse_mobi()
        elif header_type == b'CONT':
            self.type = 'CONT'
            self.parse_cont()
        else:
            raise azw2zipException(u'invalid header: {}'.format((binascii.hexlify(header_type)).decode('ascii')))

    def parse_mobi(self, dump = False):
        self.mobi_header_offset = 0x10
        mobi_header = self.header[self.mobi_header_offset:]
        mobi_header_size, = struct.unpack_from(b'>L', mobi_header, 0x04)

        self.version, = struct.unpack_from(b'>L', mobi_header, 0x14)
        if self.version != 8 and self.version != 6 and self.version != 4:
            raise azw2zipException(u'invalid mobi version: {}'.format(self.version))

        self.codepage, = struct.unpack_from(b'>L', mobi_header, 0x0C)
        codec_map = {
            1252 : 'windows-1252',
            65001: 'utf-8',
        }
        if self.codepage in codec_map:
            self.codec = codec_map[self.codepage]
        if not dump:
            self.add_meta_data('Codec', self.codec)

        title_offset, = struct.unpack_from(b'>L', mobi_header, 0x44)
        title_length, = struct.unpack_from(b'>L', mobi_header, 0x48)
        title = self.header[title_offset:title_offset+title_length].decode(self.codec, errors='replace')
        if not dump:
            self.add_meta_data('Title', title)

        self.first_resc_offset, = struct.unpack_from(b'>L', mobi_header, 0x5C)

        if dump:
            print(u"")
            print(u"Type: {}".format(self.type))
            print(u"Version: {}".format(self.version))
            print(u"Codec: {0:s}".format(self.codec))
            print(u"Title: {0:s}".format(self.meta_data.get('Title')[0]))
            print(u"first_resc_offset: {0:d}".format(self.first_resc_offset))

        exth_flag, = struct.unpack_from(b'>L', mobi_header, 0x70)
        self.exth = b''
        self.exth_offset = 0
        self.exth_size = 0
        if exth_flag & 0x40:
            self.exth_offset = mobi_header_size
            if mobi_header[self.exth_offset:self.exth_offset+0x04] != b'EXTH': #b'\x45\x58\x54\x48':
                raise azw2zipException(u'invalid EXTH header: {}'.format(mobi_header[self.exth_offset:self.exth_offset+0x04]))
            self.exth_size, = struct.unpack_from(b'>L', mobi_header, self.exth_offset+0x04)
            self.exth_size = ((self.exth_size + 3)>>2)<<2  # round to next 4 byte boundary
            self.exth = mobi_header[self.exth_offset:self.exth_offset + self.exth_size]

            self.parse_exth(dump)

    def parse_cont(self, dump = False):
        self.mobi_header_offset = 0
        cont_header = self.header[self.mobi_header_offset:]
        cont_header_size, = struct.unpack_from(b'>L', cont_header, 0x04)

        self.codepage, = struct.unpack_from(b'>L', cont_header, 0x0C)
        codec_map = {
            1252 : 'windows-1252',
            65001: 'utf-8',
        }
        if self.codepage in codec_map:
            self.codec = codec_map[self.codepage]
        if not dump:
            self.add_meta_data('Codec', self.codec)

        title_offset, = struct.unpack_from(b'>L', cont_header, 0x28)
        title_length, = struct.unpack_from(b'>L', cont_header, 0x2c)
        title = self.header[title_offset:title_offset+title_length].decode(self.codec, errors='replace')
        if not dump:
            self.add_meta_data('Title', title)

        #self.first_resc_offset, = struct.unpack_from(b'>L', cont_header, 0x5C)
        self.first_resc_offset = 1

        self.version, = struct.unpack_from(b'>L', cont_header, 0x14)
        #if self.version != 8:
        #    raise azw2zipException(u'invalid mobi version: {}'.format(self.version))

        if dump:
            print(u"")
            print(u"Type: {}".format(self.type))
            print(u"Version: {}".format(self.version))
            print(u"Codec: {0:s}".format(self.codec))
            print(u"Title: {0:s}".format(self.meta_data.get('Title')[0]))
            print(u"first_resc_offset: {0:d}".format(self.first_resc_offset))

        self.exth = b''
        self.exth_offset = 0x30
        if cont_header[self.exth_offset:self.exth_offset+0x04] != b'EXTH': #b'\x45\x58\x54\x48':
            raise azw2zipException(u'invalid EXTH header: {}'.format(cont_header[self.exth_offset:self.exth_offset+0x04]))
        self.exth_size, = struct.unpack_from(b'>L', cont_header, self.exth_offset+0x04)
        self.exth_size = ((self.exth_size + 3)>>2)<<2  # round to next 4 byte boundary
        self.exth = cont_header[self.exth_offset:self.exth_offset + self.exth_size]

        self.parse_exth(dump)

    def parse_exth(self, dump = False):
        if not self.exth:
            return

        if dump:
            print(u"")
            print(u"EXTH metadata Offset:0x{:08X} Padded Size:{:,d}(0x{:08X})".format(self.mobi_header_offset+self.exth_offset, self.exth_size, self.exth_size))
            print(u"Key Offset     Size Decription                     Value")
            print(u"=== ---------- ---- ------------------------------ -----")

        exth_count, = struct.unpack_from(b'>L', self.exth, 0x08)
        offset = 0x0C
        for _ in range(exth_count):
            id, size = struct.unpack_from(b'>LL', self.exth, offset)
            content = self.exth[offset+8:offset+size]
            content_size = size - 8
            #
            if id in self.id_map_strings:
                name = self.id_map_strings[id]
                value = content.decode(self.codec, errors='replace')
                if not dump:
                    self.add_meta_data(name, value)
                else:
                    try:
                        print(u'{0: >3d} 0x{1:08X} {2: >4d} {3: <30s} {4:s}'.format(id, offset, content_size, name, value))
                    except UnicodeEncodeError:
                        print(u'{0: >3d} 0x{1:08X} {2: >4d} {3: <30s} {4:s}'.format(id, offset, content_size, name, value.encode('cp932', 'replace').decode('cp932')))
            elif id in self.id_map_values:
                name = self.id_map_values[id]
                if size == 9:
                    value, = struct.unpack(b'B',content)
                    if not dump:
                        self.add_meta_data(name, value)
                    else:
                        print(u'{0: >3d} 0x{1:08X} byte {2:<30s} {3:d}'.format(id, offset, name, value))
                elif size == 10:
                    value, = struct.unpack(b'>H',content)
                    if not dump:
                        self.add_meta_data(name, value)
                    else:
                        print(u'{0: >3d} 0x{1:08X} word {2:<30s} 0x{3:0>4X} ({3:d})'.format(id, offset, name, value))
                elif size == 12:
                    value, = struct.unpack(b'>L',content)
                    if not dump:
                        self.add_meta_data(name, value)
                    else:
                        print(u'{0: >3d} 0x{1:08X} long {2:<30s} 0x{3:0>8X} ({3:d})'.format(id, offset, name, value))
                else:
                    if dump:
                        value = (binascii.hexlify(content)).decode('ascii')
                        print(u'{0: >3d} 0x{1:08X} {2: >4d} {3: <30s} (0x{4:s})'.format(id, offset, content_size, u"Bad size for "+name, value))
            else:
                name = u"Unknown EXTH ID {0:d}".format(id)
                if dump:
                    value = (binascii.hexlify(content)).decode('ascii')
                    print(u"{0: >3d} 0x{1:08X} {2: >4d} {3: <30s} 0x{4:s}".format(id, offset, content_size, name, value))
            #
            offset += size

    def dump(self):
        if self.type == 'MOBI':
            self.parse_mobi(True)
        elif self.type == 'CONT':
            self.parse_cont(True)

        for image_keys in self.image_data:
            print("{0: >3d} : {1:}".format(image_keys, self.image_data[image_keys]))

    def set_sec_count(self, count):
        self.sec_count = count

    def get_sec_count(self):
        return self.sec_count

    def get_type(self):
        return self.type

    def get_version(self):
        return self.version

    def get_meta_data(self):
        return self.meta_data

    def get_image_data(self):
        return self.image_data

    def get_sec_offset(self):
        return self.sec_offset

    def get_first_resc_offset(self):
        return self.first_resc_offset

    def add_meta_data(self, name, value):
        if name not in self.meta_data:
            self.meta_data[name] = [value]
        else:
            self.meta_data[name].append(value)

    def add_image_data(self, sec_offset, img_offset, img_size, img_type):
        self.image_data[sec_offset - self.first_resc_offset + 1] = [img_offset, img_size, img_type]

    def open(self):
        if self.f and not self.f.closed:
            return self.f

        if not self.fpath:
            return None

        f = open(self.fpath, "rb")
        self.f = f

        return f

    def close(self):
        if self.f and not self.f.closed:
            self.f.close()

    def read(self, offset, size):
        self.f.seek(offset)
        data = self.f.read(size)

        return data

class azw_file:
    def __init__(self):
        self.debug = False

        self.sec_count = 0
        self.sec_count_offset = 0x4C
        self.sec_info_offset = 0x4E
        self.print_replica = False

    def load(self, fpath, azw_header_data, debug = False):
        self.debug = debug

        if self.debug:
            print(u"")
            print(u"Load: {}".format(fpath))

        if not os.path.exists(fpath):
            raise azw2zipException(u'file not found: {}'.format(fpath))

        f = open(fpath, "rb")
        header = f.read(0x4E)

        if header[:8] == b'\xEA\x44\x52\x4D\x49\x4F\x4E\xEE':
            f.close()
            #print(u'unspported DRM ebook: {}'.format(fpath))
            #return 1
            raise azw2zipException(u'unspported DRM ebook: {}'.format(fpath))

        ident = header[0x3C:0x3C+8]
        if not ident in [b'BOOKMOBI' ,b'RBINCONT']:
            f.close()
            #print(u'invalid file format: {}'.format(ident))
            #return 1
            raise azw2zipException(u'invalid file format: 0x{}'.format((binascii.hexlify(ident)).decode('ascii')))

        self.sec_count, = struct.unpack_from(b'>H', header, self.sec_count_offset)

        if self.debug:
            print(u" Sec Offset           Size(Hex Size  ) Description")
            print(u"==== ---------- ---------------------- -------------")

        header_index = len(azw_header_data)
        sec_header = f.read(self.sec_count * 8)
        sec_offset = 0
        for sec_index in range(self.sec_count):
            sec_start, = struct.unpack_from(b'>L', sec_header, sec_index * 8)
            if sec_index == self.sec_count -1:
                sec_end = os.path.getsize(fpath)
            else:
                sec_end, = struct.unpack_from(b'>L', sec_header, (sec_index + 1) * 8)
            sec_size = sec_end - sec_start

            f.seek(sec_start)
            if sec_size < 0x10:
                sec_type10 = f.read(sec_size)
            else:
                sec_type10 = f.read(0x10)
            if sec_size < 4:
                sec_type = sec_type10[:sec_size]
            else:
                sec_type = sec_type10[:4]
            if sec_type == b'\x44\x48\x00\x00' or sec_type == b'\x00\x01\x00\x00' or sec_type == b'\x00\x02\x00\x00':
                if self.debug:
                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) MOBI_Header".format(sec_index, sec_start, sec_size, sec_size))
                f.seek(sec_start)
                header = f.read(sec_size)
                header_offset = sec_start
                header_size = sec_size
                if header[0x10:0x14] == b'MOBI': #b'\x4D\x4F\x42\x49':
                    mobi_header = azw_header(fpath, self.debug)
                    mobi_header.set_header(sec_index, header, header_size, header_offset)
                    #mobi_header.parse_mobi(False)
                    #
                    if azw_header_data:
                        azw_header_data[header_index-1].set_sec_count(sec_offset)
                    azw_header_data.append(mobi_header)
                    if mobi_header.get_version() == 4:
                        self.print_replica = True
                    sec_offset = 0
                    continue
                else:
                    raise azw2zipException(u'invalid header: {}'.format(mobi_header[self.mobi_header_offset:self.mobi_header_offset+0x04]))
            elif sec_type == b'CONT': #b'\x43\x4F\x4E\x54':
                if sec_type10[:0xC] == b'CONTBOUNDARY':
                    if self.debug:
                        print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) CONTAINER BOUNDARY".format(sec_index, sec_start, sec_size, sec_size))
                else:
                    if self.debug:
                        print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) CONT_Header".format(sec_index, sec_start, sec_size, sec_size))
                    f.seek(sec_start)
                    header = f.read(sec_size)
                    header_offset = sec_start
                    header_size = sec_size
                    #
                    cont_header = azw_header(fpath, self.debug)
                    cont_header.set_header(sec_index, header, header_size, header_offset)
                    #cont_header.parse_cont(False)
                    #
                    if azw_header_data:
                        azw_header_data[header_index-1].set_sec_count(sec_offset)
                    azw_header_data.append(cont_header)
                    if cont_header.get_version() == 4:
                        self.print_replica = True
                    sec_offset = 0
                    continue
            elif sec_type == b'CRES': #b'\x43\x52\x45\x53':
                f.seek(sec_start + 0x0C)
                cres_data = f.read(0x20)
                img_type = self.get_image_type(cres_data)
                if self.debug:
                    #if cres_data[:3] == b'\xff\xd8\xff':
                    if img_type:
                        print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) CRES({4:}_Image)".format(sec_index, sec_start, sec_size, sec_size, img_type))
                    else:
                        print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) CRES(Unknown_Image)".format(sec_index, sec_start, sec_size, sec_size))
                azw_header_data[header_index].add_image_data(sec_offset, sec_start + 0x0C, sec_size - 0x0C, img_type)
            elif sec_type == b'\xA0\xA0\xA0\xA0':
                if self.debug:
                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) Empty_Image/Resource_Placeholder".format(sec_index, sec_start, sec_size, sec_size))
            elif sec_type10[:8] == b'BOUNDARY':
                header_index += 1
                if self.debug:
                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) BOUNDARY".format(sec_index, sec_start, sec_size, sec_size))
            elif sec_type == b'\xe9\x8e\x0d\x0a':
                if self.debug:
                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) EOF_RECORD".format(sec_index, sec_start, sec_size, sec_size))
                break
            else:
                f.seek(sec_start)
                if sec_size < 0x20:
                    img_header = f.read(sec_size)
                else:
                    img_header = f.read(0x20)
                img_type = self.get_image_type(img_header)
                if img_type:
                    if self.debug:
                        print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) {4:}_Image".format(sec_index, sec_start, sec_size, sec_size, img_type))
                    azw_header_data[header_index].add_image_data(sec_offset, sec_start, sec_size, img_type)
                else:
                    if self.debug:
                        if sec_type in [b"FLIS", b"FCIS", b"FDST", b"DATP", b"SRCS", b"PAGE", b"CMET", b"FONT", b"RESC", b"CDIC", b"HUFF", b"INDX", b"GESW", b"kind"]:
                            print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) {4:}".format(sec_index, sec_start, sec_size, sec_size, sec_type))
                        else:
                            value = (binascii.hexlify(sec_type)).decode('ascii')
                            if sec_type.isalnum():
                                try:
                                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) Unknown({4:})".format(sec_index, sec_start, sec_size, sec_size, sec_type))
                                except UnicodeDecodeError:
                                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) Unknown(0x{4:})".format(sec_index, sec_start, sec_size, sec_size, value))
                                except UnicodeEncodeError:
                                    print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) Unknown(0x{4:})".format(sec_index, sec_start, sec_size, sec_size, value))
                            else:
                                print(u"{0:4} 0x{1:08X} {2: >10,d}(0x{3:08X}) Unknown(0x{4:})".format(sec_index, sec_start, sec_size, sec_size, value))
            sec_offset += 1

        if azw_header_data:
            azw_header_data[header_index-1].set_sec_count(sec_offset)

        f.close()

        return 0

    def get_image_type(self, imgdata):
        # need 0x20 bytes
        imgtype = imghdr.what(u'', imgdata)
        if imgtype == "jpeg":
            return JPEG_EXT

        if imgtype is None:
            if imgdata[0:3] == b'\xFF\xD8\xFF':
                imgtype = JPEG_EXT
        return imgtype

    def get_sec_count(self):
        return self.sec_count

    def is_print_replica(self):
        return self.print_replica

class azw2zip:

    def __init__(self):
        self.debug = False
        self.image_data = []
        self.azw_header_data = []
        self.print_replica = False

    def load(self, azw_fpath, res_fpath = u'', debug = False):
        self.debug = debug

        azw = azw_file()
        azw.load(azw_fpath, self.azw_header_data, self.debug)
        self.print_replica = azw.is_print_replica()

        if res_fpath:
            res = azw_file()
            res.load(res_fpath, self.azw_header_data, self.debug)
            if res.is_print_replica():
                self.print_replica = True

        if self.debug:
            for header_info in self.azw_header_data:
                header_info.dump()

        return 0

    def get_image_info(self, offset):
        header = None
        image_info = None
        for info in self.azw_header_data:
            if info.get_type() == 'CONT' and info.get_image_data().get(offset):
                return info, info.get_image_data().get(offset)
            if info.get_image_data().get(offset):
                header = info
                image_info = info.get_image_data().get(offset)

        return header, image_info

    def is_print_replica(self):
        return self.print_replica

    def get_meta_data(self, index = 0):
        return self.azw_header_data[index].get_meta_data()

    def open_azw_header(self):
        for info in self.azw_header_data:
            info.open()

    def close_azw_header(self):
        for info in self.azw_header_data:
            info.close()

    def make_output_image_info(self, cfg):
        # 画像情報作成
        self.image_data = []

        meta_data = self.get_meta_data()

        cover_offset = int(meta_data.get('CoverOffset', ['-1'])[0])
        thumb_offset = int(meta_data.get('ThumbOffset', ['-1'])[0])

        # カバー画像があれば最初に追加
        if cover_offset != -1:
            image_header, image_info = self.get_image_info(cover_offset)
            if image_info:
                num = len(self.image_data)
                image_fname = cfg.getCoverFilename().format(sec_num0=cover_offset, sec_num1=cover_offset+1, num0=num, num1=num+1, ext=image_info[2])
                self.image_data.append([image_header, image_fname, image_info[0], image_info[1]])

        #res_count = int(meta_data.get('Embedded-Record-Count', ['-1'])[0])
        sec_count = self.azw_header_data[0].get_sec_count()

        # その他の画像を追加
        image_num = 0
        for sec_index in range(sec_count+1):
            if sec_index == cover_offset:
                # カバー画像は最初に追加してあるのでスキップ
                continue

            image_header, image_info = self.get_image_info(sec_index)
            if image_info:
                num = len(self.image_data)
                image_fname = cfg.getImageFilename().format(sec_num0=sec_index, sec_num1=sec_index+1, num0=num, num1=num+1, image_num0=image_num, image_num1=image_num+1, ext=image_info[2])
                # サムネイル画像
                if sec_index == thumb_offset:
                    if not cfg.isOutputThumb():
                        continue
                    image_fname = cfg.getThumbFilename().format(sec_num0=sec_index, sec_num1=sec_index+1, num0=num, num1=num+1, ext=image_info[2])
                else:
                    image_num += 1
                self.image_data.append([image_header, image_fname, image_info[0], image_info[1]])

        if self.debug:
            print(u"")
            print(u"Image Info Count:{}".format(len(self.image_data)))
            print(u" Num      Offset          Size(Hex Size  ) Name")
            print(u"==== ---- ---------- --------------------- --------------")
            sec_index = 0
            for image_info in self.image_data:
                print(u"{0: >4d} {1:3s} 0x{2:08X} {3: >9,d}(0x{4:08X}) {5:s}".format(sec_index, image_info[0].get_type(), image_info[2], image_info[3], image_info[3], image_info[1]))
                sec_index += 1

    def output_zip(self, out_dir, cfg):
        meta_data = self.get_meta_data()
        out_fpath = os.path.join(out_dir, cfg.makeOutputFileName(meta_data) + u".zip")

        if not cfg.isOverWrite() and os.path.exists(out_fpath):
            return 1, out_fpath

        if not os.path.exists(os.path.dirname(out_fpath)):
            os.makedirs(os.path.dirname(out_fpath))

        if self.debug:
            print(u"")
            try:
                print(u"Create: {}".format(out_fpath))
            except UnicodeEncodeError:
                print(u"Create: {}".format(out_fpath.encode('cp932', 'replace').decode('cp932')))

        outzip = zipfile.ZipFile(out_fpath, 'w')

        # 日付生成
        date_time = dt.now()
        published = meta_data.get('Published')[0]
        if published:
            date_time = dt.strptime(published, '%Y-%m-%d')
        file_date_time = date_time.timetuple()

        self.open_azw_header()

        # zip書き込み
        for image_info in self.image_data:
            nzinfo = zipfile.ZipInfo(image_info[1])
            nzinfo.date_time = file_date_time
            if cfg.isCompressZip():
                nzinfo.compress_type = zipfile.ZIP_DEFLATED
            else:
                nzinfo.compress_type = zipfile.ZIP_STORED
            #TTTTsstrwxrwxrwx0000000000ADVSHR
            #^^^^____________________________ file type as explained above
            #    ^^^_________________________ setuid, setgid, sticky
            #       ^^^^^^^^^________________ permissions
            #                ^^^^^^^^________ This is the "lower-middle byte" your post mentions
            #                        ^^^^^^^^ DOS attribute bits
            #    ‭0001100000000000000000000000‬
            nzinfo.external_attr = 0o600 << 16 # make this a normal file
            #    ‭0000000000000000000000100000‬
            nzinfo.external_attr |= 0x020 # add Archive attr
            outzip.writestr(nzinfo, image_info[0].read(image_info[2], image_info[3]))

        self.close_azw_header()

        outzip.close()

        return 0, out_fpath

    def output_directory(self, out_dir, cfg):
        meta_data = self.get_meta_data()
        out_fpath = os.path.join(out_dir, cfg.makeOutputFileName(meta_data))

        if not cfg.isOverWrite() and os.path.exists(out_fpath):
            return 1, out_fpath

        if not os.path.exists(out_fpath):
            os.makedirs(out_fpath)

        if self.debug:
            print(u"")
            try:
                print(u"Create: {}".format(out_fpath))
            except UnicodeEncodeError:
                print(u"Create: {}".format(out_fpath.encode('cp932', 'replace').decode('cp932')))

        self.open_azw_header()

        # 画像出力
        for image_info in self.image_data:
            fpath = os.path.join(out_fpath, image_info[1])
            with open(fpath, 'wb') as f:
                f.write(image_info[0].read(image_info[2], image_info[3]))

        self.close_azw_header()

        return 0, out_fpath

def usage(progname):
    print(u"Description:")
    print(u"  azw to zip file.")
    print(u"  ")
    print(u"Usage:")
    print(u"  {} [-zftscomd] <azw_indir> [outdir]".format(progname))
    print(u"  ")
    print(u"Options:")
    print(u"  -z        zipを出力(出力形式省略時のデフォルト)")
    print(u"  -f        画像ファイルをディレクトリに出力")
    print(u"  -t        ファイル名の作品名にUpdated_Titleを使用する(Kindleと同じ作品名)")
    print(u"  -s        作者名を昇順でソートする")
    print(u"  -c        zipでの出力時に圧縮をする")
    print(u"  -o        出力時に上書きをする(デフォルトは上書きしない)")
    print(u"  -m        サムネイル画像を出力する")
    print(u"  -d        デバッグモード(各種ログ表示)")
    print(u"  azw_indir 変換する書籍のディレクトリ(再帰的に読み込みます)")
    print(u"  outdir    出力先ディレクトリ(省略時は{}と同じディレクトリ)".format(progname))

def find_all_files(directory):
    for root, dirs, files in os.walk(directory):
        # yield root
        for file in files:
            yield os.path.join(root, file)

def main(argv=sys.argv):
    progname = os.path.splitext(os.path.basename(argv[0]))[0]
    azw2zip_dir = os.path.dirname(os.path.abspath(argv[0]))

    print(u"{0:} v.{1:s}\nCopyright (C) 2020 junk2ool".format(progname, __version__))
    print(u"")

    try:
        opts, args = getopt.getopt(argv[1:], "zftscomd")
    except getopt.GetoptError as err:
        print(str(err))
        usage(progname)
        sys.exit(2)

    if len(args) < 1:
        usage(progname)
        sys.exit(2)

    cfg = azw2zipConfig()
    cfg_fpath = os.path.join(azw2zip_dir, u'{}.json'.format(progname))
    if os.path.exists(cfg_fpath):
        cfg.load(cfg_fpath)
    else:
        cfg.load(os.path.join(azw2zip_dir, u'azw2zip.json'))

    updated_title = cfg.isUpdatedTitle()
    authors_sort = cfg.isAuthorsSort()
    compress_zip = cfg.isCompressZip()
    over_write = cfg.isOverWrite()
    output_thumb = cfg.isOutputThumb()
    output_zip = cfg.isOutputZip()
    output_images = cfg.isOutputImages()

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
        if o == "-f":
            output_images = True
        if o == "-d":
            debug_mode = True
    if not output_zip and not output_images:
        output_zip = True
    cfg.setOptions(updated_title, authors_sort, compress_zip, over_write, output_thumb, debug_mode)
    cfg.setOutputFormats(output_zip, False, output_images, False)
    
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
    if not os.path.exists(out_dir):
        os.path.mkdirs(out_dir)
        print(u"出力ディレクトリ: 作成: {}".format(out_dir))

    # 処理ディレクトリのファイルを再帰走査
    for azw_fpath in find_all_files(in_dir):
        a2z = azw2zip()

        # ファイルでなければスキップ
        if not os.path.isfile(azw_fpath):
            continue
        # .azwファイルでなければスキップ
        fext = os.path.splitext(azw_fpath)[1].upper()
        if fext not in ['.AZW', '.AZW3', '.AZW4', '.MOBI']:
            continue

        print(u"")
        azw_dir = os.path.dirname(azw_fpath)
        print(u"変換開始: {}".format(azw_dir))

        # HD画像(resファイル)検索
        res_fpath = u''
        res_files = glob.glob(os.path.join(os.path.dirname(azw_fpath), u'*.res'))
        if res_files:
            res_fpath = res_files[0]

        print(u" 書籍変換: 開始: {}".format(azw_fpath))

        # azw(+res)読み込み
        try:
            if a2z.load(azw_fpath, res_fpath, debug_mode) != 0:
                continue
        except azw2zipException as e:
            print(str(e))
            continue

        cfg.setPrintReplica(a2z.is_print_replica())

        a2z.make_output_image_info(cfg)

        # Directory出力
        if cfg.isOutputImages():
            ret,out_fpath = a2z.output_directory(out_dir, cfg)
            output_status = u'失敗'
            if ret == 0:
                output_status = u'完了'
            elif ret == 1:
                output_status = u'パス'
            try:
                print(u" 画像出力: {}: {}".format(output_status, out_fpath))
            except UnicodeEncodeError:
                print(u" 画像出力: {}: {}".format(output_status, out_fpath.encode('cp932', 'replace').decode('cp932')))

        # zip出力
        if cfg.isOutputZip():
            ret,out_fpath = a2z.output_zip(out_dir, cfg)
            output_status = u'失敗'
            if ret == 0:
                output_status = u'完了'
            elif ret == 1:
                output_status = u'パス'
            try:
                print(u" zip変換: {}: {}".format(output_status, out_fpath))
            except UnicodeEncodeError:
                print(u" zip変換: {}: {}".format(output_status, out_fpath.encode('cp932', 'replace').decode('cp932')))

        print(u"変換完了: {}".format(azw_dir))

    return 0

if __name__ == '__main__':
	sys.exit(main())
