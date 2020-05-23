#!/usr/bin/env python

import sys
import csv
import json

"""

## Usage

jpost_rome_to_json.py (csv_file)

ken_all_rome.csv

## Input

- 日本郵便トップ > 郵便番号検索 > 郵便番号データダウンロード > 住所の郵便番号（ローマ字・zip形式）
- 全国一括のデータファイル　（2019年6月現在）

% curl -o - 'https://www.post.japanpost.jp/zipcode/dl/roman/ken_all_rome.zip' | tar -xf - -O | nkf -w > jpost-rome.csv

% head -5 ken_all_rome.csv
"0600000","北海道","札幌市　中央区","以下に掲載がない場合","HOKKAIDO","SAPPORO SHI CHUO KU","IKANIKEISAIGANAIBAAI"
"0640941","北海道","札幌市　中央区","旭ケ丘","HOKKAIDO","SAPPORO SHI CHUO KU","ASAHIGAOKA"
"0600041","北海道","札幌市　中央区","大通東","HOKKAIDO","SAPPORO SHI CHUO KU","ODORIHIGASHI"
"0600042","北海道","札幌市　中央区","大通西（１〜１９丁目）","HOKKAIDO","SAPPORO SHI CHUO KU","ODORINISHI(1-19-CHOME)"
"0640820","北海道","札幌市　中央区","大通西（２０〜２８丁目）","HOKKAIDO","SAPPORO SHI CHUO KU","ODORINISHI(20-28-CHOME)"

## Output

cities_rome = {
    "愛知県": "1000020230006",
    "愛知県名古屋市": "3000020231002",
    "愛知県豊橋市": "3000020232025",
    ...
};

"""

import argparse

def roman_canon(src):
    n = src.split(' ')
    if len(n) > 1:
        return "{}-{}".format(n[0].capitalize(), n[1].lower())
    else:
        return "{}".format(n[0].capitalize())

ap = argparse.ArgumentParser()
ap.add_argument("csv_rome", help="CSV file of the name of citeis and ROME-JI.")
ap.add_argument("-i", action="store", dest="indent", type=int,
                help="specify the number of columns for indent. e.g. -i 4")
ap.add_argument("-s", action="store", dest="skip_lines", type=int, default=0,
                help="""specify the number of lines at the header
                in the file to skip.""")
ap.add_argument("-x", action="store_true", dest="transx",
                help="enable to make a dict for other program (e.g. python).")
opt = ap.parse_args()

rome_dict = {}
with open(opt.csv_rome) as fd:
    it = csv.reader(fd, dialect=csv.excel)
    for _ in range(opt.skip_lines):
        it.__next__()
    for row in it:
        # pref name, XXX loosy
        pref_name = "{}".format(row[1])
        pref_romaji = "{}".format(roman_canon(row[4]))
        rome_dict.update({ pref_name: pref_romaji })
        # city name
        city_name = "{}{}".format(pref_name, row[2].split('　')[0])
        city_romaji = "{}, {}".format(pref_romaji, roman_canon(row[5]))
        rome_dict.update({ city_name: city_romaji })

if opt.transx:
    print("cities_rome = ", end="")

print(json.dumps(rome_dict, indent=opt.indent, ensure_ascii=False))

