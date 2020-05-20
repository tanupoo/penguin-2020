IMPLEMENTATION NOTE
===================

## User-side: Browser (Chrome, Firefox)

- list view / entry form

    + entry formは、イメージを固めるためにまずはスクラッチで書く。
    + [DataTables](https://datatables.net/): [github](https://github.com/DataTables/DataTables): version ?
    + [jquery](https://jquery.com/): [github](https://github.com/jquery/jquery): version 3.3.1
    + [datetimepicker](https://xdsoft.net/jqplugins/datetimepicker/): [github](https://github.com/xdan/datetimepicker): version ?
    + select2-to-tree: [github](https://github.com/clivezhg/select2-to-tree): version ?
    + [select2](https://select2.org/): [github](https://github.com/select2/select2): version ?
    + [modaal](http://humaan.com/modaal/): [github](https://github.com/humaan/Modaal): version ?

## Server-side: HTTPサーバ

- まずは融通が効くので aiohttpだけで書く。
- そのうち FastAPI あたりに置き換える。

## Server-side: Database: MongoDB

- db: plod
- collection: draft
- port: 27017
- username: XXX 決め打ち？
- password: XXX 決め打ち？

## Docker

- インターネット未接続でも使えるようにする。
- クラウド版、オンプレ版、2種類用意するか？

## データモデル

```
DATE = YYYY-mm-dd
TIME = HH:MM

PLH_MEMBERS = {
    "departureDate": DATE(CHOICE),
    "departureTime": TIME(CHOICE),
    "departureFrom": LOCATION(CHOICE),
    "departureFromAnnex": STRING(FREE),
    "arrivalDate": DATE(CHOICE),
    "arrivalTime": TIME(CHOICE),
    "arrivalIn": LOCATION(CHOICE),
    "arrivalInAnnex": STRING(FREE),
    "vehicles": [ VEHICLES ],
    "details": STRING(FREE),
};

PCH_MEMBERS = {
    "conditionDate": DATE(CHOICE),
    "conditionTime": TIME(CHOICE),
    "conditions": [ CONDITIONS ],
    "details": STRING(FREE),
};

PLOD = {
    "dataSource": STRING(FREE),
    "publisher": STRING(CHOICE),
    "publisherOthers": STRING(FREE),
    "localId": STRING(FREE),
    "localSubId": STRING(FREE),
    "disease": STRING(CHOICE),
    "diseaseOthers": STRING(FREE),
    "dateConfirmed": STRING(CHOICE),
    "age": STRING(CHOICE),
    "gender": STRING(CHOICE),
    "residence": STRING(CHOICE),
    "residenceAnnex": STRING(FREE),
    "closeContacts": STRING(FREE),
    "locationHistory": [
	PLH_MEMBERS
    ],
    "conditionHistory": [
	PCH_MEMBERS
    ],
    "createdTime": STRING(ISO_DATE_TIME) or NULL,
    "updatedTime": STRING(ISO_DATE_TIME) or NULL,
};
```

サーバからの応答の例。

```
TBD
```

## インターフェイス

- GET /crest

PLODを入力するエントリーフォームを返す。

return:

    200 エントリーフォーム

- POST /beak

JSON形式のPLODを受け取り、データベースに登録する。

    { PLOD }

return:

    "result": { "plod": { PLOD } }

curl を使用した例:

```
% curl -X POST -d@data.json -k https://plod.server/beak
{"msg_type": "response", "status": 200, "ts": "2020-03-29T09:23:20.560907", "result": {"event_id": "0731f36c-51fb-41f7-b808-f63d125548a3"}}
```

- POST /beak/bulk

JSON形式のPLODのリストを受け取り、データベースに登録する。

input:

    [ { PLOD }, ... ]

    or 

    { "result": "...", "plod": [ { PLOD }, ... ] }

return:

    "result": "success"

- DELETE /tail

reportIdを受け取り、PLODを削除する。

return:

    "result": "success"
    "result": other than "success"

```
% curl -X DELETE -k https://plod.server/tail/0731f36c-51fb-41f7-b808-f63d125548a3
{"msg_type": "response", "status": 200, "ts": "2020-03-29T09:23:20.560907", "result": "success"}
```

- GET /tummy

PLODのリスト表示とダウンロードするフォームを返す。

return:

    200 HTML

- GET /tummy/{type}/{CONDITION}

指定した条件に該当する PLODs を、JSON形式と Turtle形式で返す。

    + GET /tummy/json/{CONDITION}
    + GET /tummy/turtle/{CONDITION}

{CONDITION}の部分は下記いずれか。

    + "all"
        * e.g. GET /tummy/json/all
        * e.g. GET /turtle/json/all
    + reportId
        * GET /tummy/json/1ef3c491-a892-4410-b4db-dc755c656cd1
        * GET /tummy/turtle/1ef3c491-a892-4410-b4db-dc755c656cd1

- JSON形式

    { "result": "success", "plod": [ PLODs ] }

該当する PLODがなかった場合は、空のPLODが帰る。

    { "result": "success", "plod": [] }

curl を使用した例:

```
% curl https://plod.server/tummy/json/2c5c6a22-c1b3-4097-b119-dad4c1ba57b9
{"result": "success", "plod": [{"publisher": "千葉県", "publisherOthers": "", "localId": "13", "localSubId": "1", "disease": "COVID-2019", "diseaseOthers": "", "dateConfirmed": "2020-01-31", "age": "20s", "gender": "Female", "residence": "千葉県", "residenceAnnex": "", "locationHistory": [{"departureDate": "2020-01-16", "departureTime": "", "departureFrom": "千葉県", "departureFromAnnex": "", "arrivalDate": "2020-01-16", "arrivalTime": "", "arrivalIn": "大阪府", "arrivalInAnnex": "", "vehicles": ["Airplane"], "vehicleOthers": "", "details": ""}, {"departureDate": "2020-01-17", "departureTime": "", "departureFrom": "大阪府", "departureFromAnnex": "", "arrivalDate": "2020-01-22", "arrivalTime": "", "arrivalIn": "Others", "arrivalInAnnex": "ツアー", "vehicles": ["Bus"], "vehicleOthers": "", "details": ""}, {"departureDate": "2020-01-22", "departureTime": "", "departureFrom": "大阪府", "departureFromAnnex": "", "arrivalDate": "2020-01-22", "arrivalTime": "", "arrivalIn": "千葉県", "arrivalInAnnex": "", "vehicles": ["Bus"], "vehicleOthers": "", "details": ""}, {"departureDate": "2020-01-29", "departureTime": "", "departureFrom": "千葉県", "departureFromAnnex": "", "arrivalDate": "2020-01-29", "arrivalTime": "", "arrivalIn": "千葉県", "arrivalInAnnex": "医療機関", "vehicles": ["Unknown"], "vehicleOthers": "", "details": ""}, {"departureDate": "2020-01-30", "departureTime": "", "departureFrom": "千葉県", "departureFromAnnex": "", "arrivalDate": "2020-01-30", "arrivalTime": "", "arrivalIn": "千葉県", "arrivalInAnnex": "医療機関", "vehicles": ["Unknown"], "vehicleOthers": "", "details": ""}], "conditionHistory": [{"conditionDate": "2020-01-20", "conditionTime": "", "conditions": ["Cough", "RunnyNose"], "conditionOthers": "", "details": ""}, {"conditionDate": "2020-04-29", "conditionTime": "", "conditions": ["RunnyNose"], "conditionOthers": "", "details": ""}], "reportId": "2c5c6a22-c1b3-4097-b119-dad4c1ba57b9", "_id": "5e8b5e53d0126b2bb98dc120"}]}
```

理想的には

    + GET /tummyjson/publisher/千葉県
    + GET /tummyjson/departureFrom/大阪府

とかできるとRESTぽいが、それはユースケースがこなれてきてから実装する。

- POST /tummy/{type}/{CONDITIOON}

指定した条件に該当する PLODs を返す。GET /tummy も参照のこと。

    + POST /tummy/json/{CONDITION}
    + POST /tummy/turtle/{CONDITION}

MongoDBのfilterをそのまま bodyにセットして POST する。
セキュリティホールになるかも？だけど、今はとりあえず提供することを考える。

curlを使用した例:

```
% curl -k -X POST -H'content-type: application/json; charset=utf-8' -d '{ "locationHistory": {"$elemMatch": { "departureFrom": "東京都" }}}' https://plod.server/tummy/json
```

