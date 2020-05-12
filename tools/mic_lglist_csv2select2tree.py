#!/usr/bin/env python

import sys
import csv
import json

"""
## Usage

python miclglist_csv2select2tree.py mic-lglist-000618153.csv > lglist-select2-20200327.js

## Output

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

initial_code = "010006" # for skip the header.

enable_javascript = True
enable_compress = True

indent = None
if enable_compress == False:
    indent = 4

def append_inc(parent, a):
    parent.append({
            "id": a,
            "text": a
            })

mydata = []
with open(sys.argv[1]) as fd:
    do_skip = True
    for row in csv.reader(fd, dialect=csv.excel):
        if do_skip is True:
            if initial_code != row[0]:
                continue
            do_skip = False
            # initialize.
            parent = { "id": row[1], "text": row[1], "inc": [] }
            continue
        if parent["id"] == row[1]:
            append_inc(parent["inc"], "".join([row[1], row[2]]))
            continue
        # next prefecture.
        mydata.append(parent)
        parent = { "id": row[1], "text": row[1], "inc": [] }

if enable_javascript:
    print("const lgList = ", end="")

print(json.dumps(mydata, indent=indent, ensure_ascii=False))

if enable_javascript:
    print(";")
