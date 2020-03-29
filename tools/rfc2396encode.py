#!/usr/bin/env python

from urllib.parse import quote
from sys import argv

# e.g.
# rfc2396encode.py '{ patientLocationHistory : { $elemMatch : { patientLocationHistoryDepartureFrom: "東京都" } } }'

if len(argv) != 2:
    exit(1)

print(quote(argv[1]), end="")
exit(0)

