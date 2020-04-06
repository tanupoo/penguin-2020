Implementations
===============

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
- そのうち tornado あたりに置き換える。

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
    "departureDate": DATE,
    "departureTime": TIME,
    "departureFrom": LOCATION,
    "departureFromAnnex": FREE_TEXT,
    "arrivalDate": DATE,
    "arrivalTime": TIME,
    "arrivalIn": LOCATION,
    "arrivalInAnnex": FREE_TEXT,
    "vehicles": [ VEHICLES ],
    "vehicleOthers": FREE_TEXT,
    "details": FREE_TEXT,
};

PCH_MEMBERS = {
    "conditionDate": DATE,
    "conditionTime": TIME,
    "conditions": [ CONDITIONS ],
    "conditionOthers": FREE_TEXT,
    "detaills": FREE_TEXT,
};

PLOD = {
    "publisher": PUBLISHER,
    "publisherOthers": FREE_TEXT,
    "localId": FREE_TEXT,
    "localSubId": FREE_TEXT,
    "disease": DISEASE,
    "diseaseOthers": FREE_TEXT,
    "dateConfirmed": DATE,
    "age": AGE,
    "gender": GENDER,
    "residence": LOCATION,
    "residenceAnnex": FREE_TEXT,
    "locationHistory": [
	PLH_MEMBERS
    ],
    "conditionHistory": [
	PCH_MEMBERS
    ],
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

return:

    "result": { "data": JSON-PLOD }

curl を使用した例:

```
% curl -X POST -d@data.json -k https://plod.server/beak
{"msg_type": "response", "status": 200, "ts": "2020-03-29T09:23:20.560907", "result": {"event_id": "0731f36c-51fb-41f7-b808-f63d125548a3"}}
```

- POST /beak/bulk

JSON形式のPLODのリストを受け取り、データベースに登録する。

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

指定した条件に該当する PLODs を、JSON形式と Turtle形式で返す。

    + GET /tummy/json/CONDITION
    + GET /tummy/turtle/CONDITION

CONDITIONの部分は下記の通り。

    + "all"
        * e.g. GET /tummy/json/all
    + reportId
        * GET /tummy/json/1ef3c491-a892-4410-b4db-dc755c656cd1
    + _id
        * GET /tummy/json/5e7d9ace0810c91d43c60130

curl を使用した例:

```
% curl -k https://plod.server/tummy/json/5e8046d40810c97060607ebe
{"msg_type": "response", "status": 200, "ts": "2020-03-29T16:04:47.326933", "result": [{"publisher": "千葉県", "localId": "13", "localSubId": "1", "disease": "COVID-2019", "dateConfirmed": "2020-01-31", "age": "20s", "gender": "Female", "residence": "千葉県", "locationHistory": [{"departureDate": "2020-01-16", "departureFrom": "東京都", "arrivalDate": "2020-01-16", "arrivalIn": "大阪府", "byTrain": true}, {"departureDate": "2020-01-22", "departureFrom": "大阪府", "arrivalDate": "2020-01-22", "arrivalIn": "東京都", "byTrain": true}], "cndHistory": [{"reportDate": "2020-01-16", "cndMalaise": true}, {"reportDate": "2020-01-22", "cndChill": true}], "reportId": "96cb3e7f-63c4-4293-affb-6a7b46432a96", "_id": "5e8046d40810c97060607ebe"}]}
```

理想的には

    + GET /tummyjson/publisher/千葉県
    + GET /tummyjson/departureFrom/大阪府

とかできるとRESTぽいが、それはユースケースがこなれてきてから実装する。

- POST /tummy

指定した条件に該当する PLODs を返す。GET /tummy も参照のこと。

    + POST /tummy/json/CONDITION
    + POST /tummy/turtle/CONDITION

MongoDBのfilterをそのまま bodyにセットして POST する。
セキュリティホールになるかも？だけど、今はとりあえず提供することを考える。

curlを使用した例:

```
% curl -k -X POST -H'content-type: application/json; charset=utf-8' -d '{ "locationHistory": {"$elemMatch": { "departureFrom": "東京都" }}}' https://plod.server/tummy/json
```

- GET /tummy の別の使い方()

MongoDBのfilterをそのまま RFC2396でエンコードした文字列をパスに指定する。

例えば、

    '{ "locationHistory": {"$elemMatch": { "departureFrom": "東京都" }}}'

ならば、

```
curl -k https://plod.server/tummy/json/`tools/rfc2396encode.py '{ "locationHistory": {"$elemMatch": { "departureFrom": "東京都" }}}' `
```

