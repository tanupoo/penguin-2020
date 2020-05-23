#!/usr/bin/env python

import csv
import json
import xlrd
import argparse

"""
## Usage

python mic_lglist_to_json.py mic-lglist.xls -x

## Input

- 総務省トップ > 政策 > 地方行財政 > 電子自治体 > 全国地方公共団体コード 
    https://www.soumu.go.jp/denshijiti/code.html
- 都道府県コード及び市区町村コード」（令和元年5月1日現在） 

curl -o mic-lglist.xls https://www.soumu.go.jp/main_content/000618153.xls

## Output with -x option

const lgList = [
    {id:1, text:"USA", inc:[
	{text:"west", inc:[
	    {id:111, text:"California", inc:[
	    {id:1111, text:"Los Angeles", inc:[
		{id:11111, text:"Hollywood"}
	    ]},
	    {id:1112, text:"San Diego"}
	    ]},
	    {id:112, text:"Oregon"}
	]}
    ]},
    {id:2, text:"India"},
    {id:3, text:"中国"}
];
"""

def make_select2(rows):

    def append_inc(parent, a):
        parent.append({
                "id": a,
                "text": a
                })

    lg_data = []
    parent = None
    for row in rows:
        if parent is not None:
            if parent["id"] == row[1].value:
                append_inc(parent["inc"], "".join([row[1].value, row[2].value]))
                continue
            else:
                # next prefecture.
                lg_data.append(parent)
                pass
        # init
        parent = { "id": row[1].value, "text": row[1].value, "inc": [] }
    return lg_data

def make_kv(rows):
    lg_data = {}
    for row in rows:
        lg_data.update({ "{}{}".format(row[1].value, row[2].value): row[0].value })
        #lg_data.update({ row[0].value: "{}{}".format(row[1].value, row[2].value) })
    return lg_data

#
# main
#
ap = argparse.ArgumentParser()
ap.add_argument("xls_file", help="XLS file taken from MIC.")
ap.add_argument("-i", action="store", dest="indent", type=int,
                help="specify the number of columns for indent. e.g. -i 4")
ap.add_argument("-s", action="store", dest="skip_lines", type=int, default=1,
                help="""specify the number of lines at the header
                in the file to skip.""")
ap.add_argument("-x", action="store_true", dest="transx",
                help="enable to make a dict for other program (e.g. select2).")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

xls_wb = xlrd.open_workbook(opt.xls_file)
if opt.debug:
    print("sheets =", xls_wb.sheet_names())
xls_sheet = xls_wb.sheet_by_index(0)

rows = xls_sheet.get_rows()
for _ in range(opt.skip_lines):
    row = rows.__next__()

if opt.transx:
    lg_data = make_select2(rows)
else:
    lg_data = make_kv(rows)

if opt.transx:
    print("const lgList = ", end="")

print(json.dumps(lg_data, indent=opt.indent, ensure_ascii=False))

if opt.transx:
    print(";")
