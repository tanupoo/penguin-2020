penguin, a PLOD server
======================

a Patient Locational Open Data (PLOD) server.

## Reference

- [Tracing patients' PLOD with mobile phones: Mitigation of epidemic risks through patients' locational open data](https://arxiv.org/abs/2003.06199)

## Acknowledgements

- Thanks to a Ms./Mr. unknown author for providing a funcy logo of PLOD penguin !
## links to the useful tools

- RDF to JSON-LD [ttl2jsonld](https://frogcat.github.io/ttl2jsonld/demo/a)
- JSON-LD to any [jsonld.js](https://github.com/digitalbazaar/jsonld.js)
- [graph viewer](https://www.kanzaki.com/works/2009/pub/graph-draw).
- many information and tools about RFD at (https://www.kanzaki.com/docs/sw/)
- [Japan local goverment list](https://www.soumu.go.jp/denshijiti/code.html)

## Requirements

- UTF-8
- User-side
    + Chrome
        * Mac: Version 80.0.3987.149
        * Windows10:
    + Firefox
        * Mac: 72.0.2
        * Windows10:
        * Windows7:
- Python3
    + pymongo
    + (plan)Tornado
- MongoDB

## Components

- User-side: Browser (Chrome, Firefox)
    + entry form
        * jquery
        * https://github.com/xdan/datetimepicker
        * https://github.com/clivezhg/select2-to-tree
- Server-side: Python3
    + PLOD Data Collector
    + RDF publisher
- Database: MongoDB

## I/F

- /crest: providing a PLOD feeder for your input.
- /beak: submittion of a PLOD.
- /tummy: providing a RDF.
- /flipper: 

## Data model

e.g.

```
{
    "publisher": "千葉県",
    "localIdentifier": "13例目,千葉県内1例目",
    "patientDisease": "covid2019",
    "dateConfirmed": "2020-01-31",
    "patientAge": "20s",
    "patientGender": "Female",
    "patientResidence": "千葉県",
    "patientLocationHistory": [
        {
            "patientLocationHistoryDepartureDate": "2020-01-16",
            "patientLocationHistoryDepartureTime": "",
            "patientLocationHistoryDepartureFrom": "東京都",
            "patientLocationHistoryArrivalDate": "2020-01-16",
            "patientLocationHistoryArrivalTime": "",
            "patientLocationHistoryArrivalTo": "大阪府",
            "transportationMethodTaxi": false,
            "transportationMethodBus": false,
            "transportationMethodTrain": true,
            "transportationMethodAirplane": false,
            "transportationMethodShip": false,
            "transportationMethodWalk": false,
            "transportationMethodFreeText": "",
            "patientLocationHistoryDetail": ""
        },
        {
            "patientLocationHistoryDepartureDate": "2020-01-22",
            "patientLocationHistoryDepartureTime": "",
            "patientLocationHistoryDepartureFrom": "大阪府",
            "patientLocationHistoryArrivalDate": "2020-01-22",
            "patientLocationHistoryArrivalTime": "",
            "patientLocationHistoryArrivalTo": "東京都",
            "transportationMethodTaxi": false,
            "transportationMethodBus": false,
            "transportationMethodTrain": true,
            "transportationMethodAirplane": false,
            "transportationMethodShip": false,
            "transportationMethodWalk": false,
            "transportationMethodFreeText": "",
            "patientLocationHistoryDetail": ""
        }
    ],
    "patientConditionHistory": [
        {
            "patientConditionHistoryDate": "2020-01-16",
            "patientConditionHistoryTime": "",
            "patientConditionHistoryStatusMalaise": true,
            "patientConditionHistoryStatusSputum": false,
            "patientConditionHistoryStatusFever": false,
            "patientConditionHistoryStatusChill": false,
            "patientConditionHistoryStatusCough": false,
            "patientConditionHistoryStatusHospitalized": false,
            "patientConditionHistoryStatusPositive": false,
            "patientConditionHistoryStatusFreeText": "",
            "patientConditionHistoryDetail": ""
        },
        {
            "patientConditionHistoryDate": "2020-01-22",
            "patientConditionHistoryTime": "",
            "patientConditionHistoryStatusMalaise": false,
            "patientConditionHistoryStatusSputum": false,
            "patientConditionHistoryStatusFever": false,
            "patientConditionHistoryStatusChill": true,
            "patientConditionHistoryStatusCough": false,
            "patientConditionHistoryStatusHospitalized": false,
            "patientConditionHistoryStatusPositive": false,
            "patientConditionHistoryStatusFreeText": "",
            "patientConditionHistoryDetail": ""
        }
    ],
    "event_id": "1ef3c491-a892-4410-b4db-dc755c656cd1",
    "_id": "ObjectId:5e7d9ace0810c91d43c60130"
}

```

## TODO

- JSON to JSON-LD to RDF, or JSON to RDF ?
- uri_prefix: 固定値 e.g. https://plod.info/data/

- moveAction
- eventId
    + event identifier, uuid, rdfs:label
- eventDate:
    + 入力した日付
- numberOfPatients:
    + 複数人ってある？
    + 一緒に行動してた場合とか？
    + 1人じゃないとデータとして意味なくない？
- publisher:
    + 自治体名のこと？
    + 入力する単位で固定か？
    + 代理入力はあるだろう。
    + であれば、初期値を定義するか。
- url:
    + データ入力時に決まらないのでは？いつ決まる？発表時に決まる？
- referencedBy
    + 入力時に決まっている？発表時かも？
    + ほぼ固定なはず。初期値を定義する。
    + 初期値は、後から追加もあるはずなので別画面でDBに入れさせて選択させる。
- healthCondition:
    + 患者の状態？
    + 選択肢いる？COVID-2019一択か？
- dateConfirmed:
    + 患者がhealthConditionになった日付？
- patientAge:
    + numberOfPatients, 複数の場合は？
- patientHomeLocation
    + https://www.j-lis.go.jp/spd/code-address/jititai-code.html
- patientGender
    + 「答えたくない」という選択肢は？
    + 医学的な見地からの性別なので入力者の客観でよいか？
- patientDisease
    + 発表を決めた時点の病名とする。
    + 履歴はpatientHealthConditionで表現する。
- infectiousDisease:
    + healthConditionで一意に決まるか？であれば、入力する必要なしか？
- MedicalCode:
    + infectiousDiseaseど同様か？

