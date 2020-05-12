#!/usr/bin/env python

import sys
import csv
import json
import re

"""

## Usage

nta_conum_csv2json.py (prefectures) (cities)

e.g.
nta_conum_csv2json.py nta-prefectures-20200512.csv nta-cities-20200512.csv > nta_conum.py

## Output

co_num = {
    "愛知県": "1000020230006",
    "愛知県名古屋市": "3000020231002",
    "愛知県豊橋市": "3000020232025",
    ...
};

## 自治体番号

taken from https://www.soumu.go.jp/denshijiti/code.html

"""

enable_compress = True
enable_python = True

skip_lines = 2 # for skipping the header.

indent = None
if enable_compress == False:
    indent = 4

csv_prefs = sys.argv[1]
csv_cities = sys.argv[2]

pref_dict = {}
with open(csv_prefs) as fd:
    it = csv.reader(fd, dialect=csv.excel)
    for _ in range(skip_lines):
        it.__next__()
    for row in it:
        pref_dict.update({ row[1]: row[0] })

def find_pref(addr):
    for k in pref_dict.keys():
        if k in addr:
            return k
    raise ValueError(f"ERROR: {addr} is not in the pref list.")

conum_dict = pref_dict.copy()
with open(csv_cities) as fd:
    it = csv.reader(fd, dialect=csv.excel)
    for _ in range(skip_lines):
        it.__next__()
    for row in it:
        pref = find_pref(row[2])
        conum_dict.update({ "".join([pref,row[1]]): row[0] })

if enable_python:
    print("co_num_dict = ", end="")

print(json.dumps(conum_dict, indent=indent, ensure_ascii=False))

