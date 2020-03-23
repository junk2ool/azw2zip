#!/usr/bin/env python
# coding: utf-8

u"""ファイル名に使えない文字を置き換える, Windows 版
https://fgshun.hatenablog.com/entry/20100213/1266032982
"""

_invalid = (
        34,  # " QUOTATION MARK
        60,  # < LESS-THAN SIGN
        62,  # > GREATER-THAN SIGN
        124, # | VERTICAL LINE
        0, 1, 2, 3, 4, 5, 6, 7,
        8, 9, 10, 11, 12, 13, 14, 15,
        16, 17, 18, 19, 20, 21, 22, 23,
        24, 25, 26, 27, 28, 29, 30, 31,
        58, # : COLON
        42, # * ASTERISK
        63, # ? QUESTION MARK
        92, # \ REVERSE SOLIDUS
        47, # / SOLIDUS
        )

table1 = {}
for i in _invalid:
    table1[i] = 95 # LOW LINE _

table2 = dict(table1)
table2.update((
        (34, 0x201d), # ”
        (60, 0xff1c), # ＜
        (62, 0xff1e), # ＞
        (124, 0xff5c), # ｜
        (58, 0xff1a), # ：
        (42, 0xff0a), # ＊
        (63, 0xff1f), # ？
        (92, 0xffe5), # ￥
        (47, 0xff0f), # ／
        ))

def safefilenames(names, table=table1, add_table=None):
    if add_table is None:
        m = table
    else:
        m = dict(table)
        m.update(add_table)
    for name in names:
        yield name.translate(m)

def safefilename(name, table=table1, add_table=None):
    return next(safefilenames([name], table, add_table))
