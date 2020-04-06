penguin, a PLOD server
======================

PLOD is short for Patient Locational Open Data.
This software has the following features.

- providing a simple entry form so that an operator can input PLOD.
- storing PLOD into No-SQL database through REST API.
- providing PLODs through REST API.

Hence, this software can help a part of #3, #4, and #5 in the picture that depicts the overview of the approach.

![the overview of the proposed approach](PLOD-overview.en.png)

Please visit the https://www.plod.info/ and see the following paper if you want to know the detail about PLOD.

- [Tracing patients' PLOD with mobile phones: Mitigation of epidemic risks through patients' locational open data](https://arxiv.org/abs/2003.06199)

## Screenshot

- view of the entry form for PLD.

<img alt="sample form" src="doc/PLOD-sample-form.png" width="640">

- view of the PLOD list.

<img alt="sample list" src="doc/PLOD-sample-list.png" width="640">

- view of the detail of a PLOD.

<img alt="sample detail" src="doc/PLOD-sample-list-detail.png" width="640">

## Docker compose

docker is available.  see and try below.

- https://github.com/tanupoo/penguin-docker

## Requirements

- Charactor encoding
    + UTF-8

- User-side
    + Chrome
        * Mac: Version 80.0.3987.149
        * Windows10:
    + Firefox
        * Mac: 72.0.2
        * Windows10:
        * Windows7:

- Python3
    + python 3.7.2.  may not work on other version.
    + pymongo
    + (plan)Tornado

- MongoDB

## Acknowledgements

- Thanks to a Ms./Mr. unknown author for providing a funcy logo of PLOD penguin !

## Links to the useful tools

- [Japan local goverment list](https://www.soumu.go.jp/denshijiti/code.html)
- RDF to JSON-LD [ttl2jsonld](https://frogcat.github.io/ttl2jsonld/demo/a)
- JSON-LD to any [jsonld.js](https://github.com/digitalbazaar/jsonld.js)
- [graph viewer](https://www.kanzaki.com/works/2009/pub/graph-draw).
- Many information and tools about RFD at (https://www.kanzaki.com/docs/sw/)

