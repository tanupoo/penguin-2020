
import sys
import re
import json

#
# given
#
report_url = "https://www.pref.chiba.lg.jp/shippei/press/2019/ncov20200131.html"
referencedBy = "https://www.pref.chiba.lg.jp/shippei/kansenshou/keihatu-index.html"
url_prefix = "https://plod.info/data"

#
# by definition
#
__content = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <https://schema.org/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gnjp: <http://geonames.jp/resource/> .
@prefix plod: <https://plod.info/property/> .
"""

"""
http://geonames.jp/resource
http://geonames.jp
"""
geoname_db_label = {
    "東京都": "gnjp:東京都",
    "大阪府": "gnjp:大阪府",
    "千葉県": "gnjp:千葉県",
    "山口県": "gnjp:山口県",
    "山口県:下関市": "gnjp:山口県下関市",
    "大分県": "gnjp:大分県",
    "福岡県": "gnjp:福岡県",
    "熊本県": "gnjp:熊本県",
}

geoname_db = {
"gnjp:東京都": """\
<http://geonames.jp/resource/東京都> a schema:Place ;
    rdfs:label "東京都" .
""",

"gnjp:大阪府": """\
<http://geonames.jp/resource/大阪府> a schema:Place ;
    rdfs:label "大阪府" .
""",

"gnjp:千葉県": """\
<http://geonames.jp/resource/千葉県> a schema:Place ;
    rdfs:label "千葉県" .
""",

"gnjp:福岡県": """\
<http://geonames.jp/resource/福岡県> a schema:Place ;
    rdfs:label "福岡県" .
""",

"gnjp:大分県": """\
<http://geonames.jp/resource/大分県> a schema:Place ;
    rdfs:label "大分県" .
""",

"gnjp:熊本県": """\
<http://geonames.jp/resource/熊本県> a schema:Place ;
    rdfs:label "熊本県" .
""",

"gnjp:山口県": """\
<http://geonames.jp/resource/山口県> a schema:Place ;
    rdfs:label "山口県" .
""",

"gnjp:山口県下関市": """\
<http://geonames.jp/resource/山口県下関市> a schema:Place ;
    rdfs:label "山口県下関市" .
""",

}

postfix = """\
<https://plod.info/entity/COVID-19> a schema:InfectiousDisease ;
    rdfs:label "COVID-19" ;
    schema:name "2019-nCoV acute respiratory disease"@en ;
    schema:infectiousAgent "2019-nCoV" ;
    schema:code <http://purl.bioontology.org/ontology/ICD10/U07.1> .

<http://purl.bioontology.org/ontology/ICD10/U07.1> a schema:MedicalCode ;
    schema:codeValue "U07.1" ;
    schema:codingSystem "ICD-10" .
"""

#
# main
#
re_transportationMethod = re.compile("^transportationMethod(.*)")
postfix_geoname = {}

def finddb(db, search_key):
    for k,v in db.items():
        if k == search_key:
            return v
    return None

def cv_publisher(a):
    # XXX need to add "厚労省"
    return finddb(geoname_db_label, a)

def cv_location(a):
    rdf_name = finddb(geoname_db_label, a)
    if rdf_name is None:
        raise Exception(f"ERROR: geoname_db_label {a} is not defeind.")
    postfix_geoname.setdefault(rdf_name, True)  # use it later.
    return rdf_name

def cv_healthCondition(a):
    db = {
        "covid2019": "https://plod.info/entity/COVID-19"
    }
    return finddb(db, a)

def plod_json2turtle(jd):
    event_id = jd["event_id"]
    publisher = cv_location(jd["publisher"])
    healthCondition = cv_healthCondition(jd["patientDisease"])
    dateConfirmed = jd["dateConfirmed"]
    patientAge = jd["patientAge"]
    patientGender = jd["patientGender"]
    patientResidence = cv_location(jd["patientResidence"])
    patient_path = f"{event_id}-P01"

    rdf = __content
    rdf += "\n"
    rdf += f'''\
<{url_prefix}/{event_id}> a schema:Event ;
    rdfs:label "{event_id}" .

<{url_prefix}/{event_id}-R01> a schema:Report ;
    rdfs:label "{event_id}-R01" ;
    schema:mainEntity <{url_prefix}/{event_id}> ;
    plod:numberOfPatients "1"^^schema:Integer ;
    schema:datePublished "{dateConfirmed}"^^schema:DateTime ;
    schema:publisher {publisher} ;
    schema:url <{report_url}> ;
    dcterms:isReferencedBy <{referencedBy}>.

<{url_prefix}/{patient_path}> a schema:Patient ;
    rdfs:label "{patient_path}" ;
    schema:subjectOf <{url_prefix}/{event_id}> ;
    schema:healthCondition <{healthCondition}> ;
    plod:dateConfirmed "{dateConfirmed}"^^schema:DateTime ;
    foaf:age "{patientAge}" ;
    schema:gender "{patientGender}" ;
    schema:homeLocation {patientResidence} .
'''

    rdf += "\n"
    labelMoveAction = 0;
    for x in jd["patientLocationHistory"]:
        labelMoveAction += 1;
        agent_path = f"{patient_path}-M{labelMoveAction:02d}"
        rdf += f'<{url_prefix}/{agent_path}> a schema:MoveAction ;\n'
        rdf += f'    rdfs:label "{agent_path}" ;\n'
        rdf += f'    schema:agent <{url_prefix}/{patient_path}> ;\n'

        if x["patientLocationHistoryDepartureDate"]:
            rdf += ('    schema:startTime "{}"^^schema:DateTime ;\n'
                    .format(x["patientLocationHistoryDepartureDate"]))

        if x["patientLocationHistoryDepartureTime"]:
            rdf += ('    schema:endTime "{}"^^schema:DateTime ;\n'
                    .format(x["patientLocationHistoryDepartureTime"]))

        if x["patientLocationHistoryDepartureFrom"]:
            rdf += ('    schema:fromLocation {} ;\n'
                    .format(cv_location(x["patientLocationHistoryDepartureFrom"])))

        if x["patientLocationHistoryArrivalTo"]:
            rdf += ('    schema:toLocation {} ;\n'
                    .format(cv_location(x["patientLocationHistoryArrivalTo"])))

        for k,v in x.items():
            if v == True:
                r = re_transportationMethod.match(k)
                if r:
                    rdf += ('    schema:instrument "{}"@ja .\n'
                        .format(r.group(1)))
        rdf += "\n"

    # Place
    for k in postfix_geoname.keys():
        geoname = finddb(geoname_db, k)
        if geoname is not None:
            rdf += geoname
            rdf += "\n"
        else:
            raise Exception(f"ERROR: geoname_db {k} is not defined.")

    # InfectiousDisease
    rdf += postfix
    return rdf
#
#
#
if __name__ == "__main__":
    if len(sys.argv) == 2:
        fd = open(sys.argv[1])
    else:
        fd = sys.stdin
    jd = json.load(fd)

    rdf = plod_json2rdf(jd)
    print(rdf)

