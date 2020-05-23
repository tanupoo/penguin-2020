#!/usr/bin/env python

import csv
import json
import xlrd
import argparse

"""

## Usage

nta_conum_to_json.py (prefs) (cities)

e.g.
nta_conum_to_json.py nta-prefs.xlsx nta-cities.xlsx > nta_conum.json

## Input

- 国税庁法人番号公表サイト
- ホーム > 法人番号とは > 国の機関等一覧
    https://www.houjin-bangou.nta.go.jp/setsumei/kuninokikanichiran.html
- 普通地方公共団体
- 都道府県(Excel形式)
- 市町村(Excel形式)

直接ダウンロードできないため、クリックして保存する。

    #curl -o nta-prefs.xlsx https://www.houjin-bangou.nta.go.jp/setsumei/images/prefectures.xlsx
    #curl -o nta-cities.xlsx https://www.houjin-bangou.nta.go.jp/setsumei/images/cities.xlsx
    <html><head><title>Request Rejected</title></head><body>The requested URL was rejected. Please consult with your administrator.<br><br>Your support ID is: 15054605593445702901<br><br><a href='javascript:history.back();'>[Go Back]</a></body></html>

## Output

{
    "愛知県": "1000020230006",
    "愛知県名古屋市": "3000020231002",
    "愛知県豊橋市": "3000020232025",
    ...
};
"""

def find_pref(addr):
    for k in pref_dict.keys():
        if k in addr:
            return k
    raise ValueError(f"ERROR: {addr} is not in the pref list.")

#
# main
#
ap = argparse.ArgumentParser()
ap.add_argument("prefs_file", help="CSV file of the prefectures.")
ap.add_argument("cities_file", help="CSV file of the cities.")
ap.add_argument("-i", action="store", dest="indent", type=int,
                help="specify the number of columns for indent. e.g. -i 4")
ap.add_argument("-s", action="store", dest="skip_lines", type=int, default=2,
                help="""specify the number of lines at the header
                in the file to skip.""")
ap.add_argument("-x", action="store_true", dest="transx",
                help="enable to make a dict for other program.")
ap.add_argument("-d", action="store_true", dest="debug",
                help="enable debug mode.")
opt = ap.parse_args()

# prefs
xls_wb = xlrd.open_workbook(opt.prefs_file)
if opt.debug:
    print("sheets =", xls_wb.sheet_names())
xls_sheet = xls_wb.sheet_by_index(0)

rows = xls_sheet.get_rows()
for _ in range(opt.skip_lines):
    row = rows.__next__()

pref_dict = {}
for row in rows:
    pref_dict.update({ row[1].value: row[0].value })

# cities
conum_dict = pref_dict.copy()

xls_wb = xlrd.open_workbook(opt.cities_file)
if opt.debug:
    print("sheets =", xls_wb.sheet_names())
xls_sheet = xls_wb.sheet_by_index(0)

rows = xls_sheet.get_rows()
for _ in range(opt.skip_lines):
    row = rows.__next__()

for row in rows:
    pref = find_pref(row[2].value)
    conum_dict.update({ "".join([pref,row[1].value]): row[0].value })

print(json.dumps(conum_dict, indent=opt.indent, ensure_ascii=False))

