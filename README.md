penguin, a PLOD server
======================

Patient Locational Open Data (PLOD)

## Components

- User-side: Browser (Chrome, Firefox)
    + Input helper
- Server-side: Python3
    + PLOD Data Collector
    + RDF publisher
- Database: MongoDB

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

## Reference

- https://arxiv.org/abs/2003.06199

## Data model

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

## JSON to RDF

- moveAction
    + startTime: 粒度は %Y-%m-%d で十分か？
    + endTime: 粒度は %Y-%m-%d で十分か？
    + fromLocation: 自治体単位か？
    + toLocation: 自治体単位か？
    + transportMethod: [電車,バス,飛行機,徒歩,自転車,バイク,タクシー]
        * 公共機関かその他かで十分かも？
        * 公共機関なら路線名もか？

- uri_prefix: 固定値 e.g. https://plod.info/data/

## 要検討

- 国籍

## Data model

```
{
    "eventId": uuid,
    "
}
```

## RDF sample

```
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <https://schema.org/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gnjp: <http://geonames.jp/resource/> .
@prefix plod: <https://plod.info/property/> .

<https://plod.info/data/12202001311> a schema:Event ;
    rdfs:label "12202001311" .

<https://plod.info/data/12202001311-R01> a schema:Report ;
    rdfs:label "12202001311-R01" ;
    schema:mainEntity <https://plod.info/data/12202001311> ;
    plod:numberOfPatients "1"^^schema:Integer ;
    schema:datePublished "2020-01-31"^^schema:DateTime ;
    schema:publisher gnjp:Chiba ;
    schema:url <https://www.pref.chiba.lg.jp/shippei/press/2019/ncov20200131.html>;
    dcterms:isReferencedBy <https://www.pref.chiba.lg.jp/shippei/kansenshou/keihatu-index.html>.

<https://plod.info/data/12202001311-P01> a schema:Patient ;
    rdfs:label "12202001311-P01" ;
    schema:subjectOf <https://plod.info/data/12202001311> ;
    schema:healthCondition <https://plod.info/entity/COVID-19> ;
    plod:dateConfirmed "2020-01-31"^^schema:DateTime ;
    foaf:age "20s" ;
    schema:gender "Female" ;
    schema:homeLocation gnjp:Chiba .

<https://plod.info/data/12202001311-P01-M01> a schema:MoveAction ;
    rdfs:label "12202001311-P01-M01" ;
    schema:agent <https://plod.info/data/12202001311-P01> ;
    schema:startTime "2020-01-16"^^schema:DateTime ;
    schema:endTime "2020-01-16"^^schema:DateTime ;
    schema:fromLocation gnjp:Tokyo ;
    schema:toLocation gnjp:Osaka ;
    schema:instrument "Airplane"@ja .

<https://plod.info/data/12202001311-P01-M02> a schema:MoveAction ;
    rdfs:label "12202001311-P01-M02" ;
    schema:agent <https://plod.info/data/12202001311-P01> ;
    schema:startTime "2020-01-22"^^schema:DateTime ;
    schema:endTime "2020-01-22"^^schema:DateTime ;
    schema:fromLocation gnjp:Osaka ;
    schema:toLocation gnjp:Tokyo ;
    schema:instrument "Bus"@ja .

<http://geonames.jp/resource/Tokyo> a schema:Place ;
    rdfs:label "Tokyo" .

<http://geonames.jp/resource/Osaka> a schema:Place ;
    rdfs:label "Osaka" .

<http://geonames.jp/resource/Chiba> a schema:Place ;
    rdfs:label "Chiba" .

<https://plod.info/entity/COVID-19> a schema:InfectiousDisease ;
    rdfs:label "COVID-19" ;
    schema:name "2019-nCoV acute respiratory disease"@en ;
    schema:infectiousAgent "2019-nCoV" ;
    schema:code <http://purl.bioontology.org/ontology/ICD10/U07.1> .

<http://purl.bioontology.org/ontology/ICD10/U07.1> a schema:MedicalCode ;
    schema:codeValue "U07.1" ;
    schema:codingSystem "ICD-10" .
```

```
<https://plod.info/data/29202001281-P01-M01> a schema:MoveAction .
    schema:agent <https://plod.info/data/29202001281-P01> ;
    schema:startTime "2020-01-08"^^schema:DateTime ;
    schema:endTime "2020-01-11"^^schema:DateTime ;
    schema:fromLocation "" ;
    schema:toLocation "" ;
    schema:instrument "Bus" .
```
