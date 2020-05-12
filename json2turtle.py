import sys
import re
import json

#
# XXX TO BE DEFINED
#
report_url = "https://www.pref.TO_BE_DEFINED.lg.jp/shippei/press/2019/ncov20200131.html"
referencedBy = "https://www.pref.TO_BE_DEFINED.lg.jp/shippei/kansenshou/keihatu-index.html"

#
# by definition
#
url_prefix = "https://plod.info/rdf"
__prefix = """\
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <https://schema.org/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix gnjp: <http://geonames.jp/resource/> .
@prefix plod: <https://plod.info/rdf/> .
"""

"""
http://geonames.jp/resource
http://geonames.jp
"""
postfix = """\
<https://plod.info/rdf/COVID-19> a schema:InfectiousDisease ;
    rdfs:label "COVID-19" ;
    schema:name "2019-nCoV acute respiratory disease"@en ;
    schema:infectiousAgent "2019-nCoV" ;
    schema:code <http://purl.bioontology.org/ontology/ICD10/U07.1> .

<http://purl.bioontology.org/ontology/ICD10/U07.1> a schema:MedicalCode ;
    schema:codeValue "U07.1" ;
    schema:codingSystem "ICD-10" .
"""

postfix_geoname = {}
postfix_publisher = {}

def finddb(db, search_key):
    for k,v in db.items():
        if k == search_key:
            return v
    return None

def add_turtle_org(base, name):
    base += f'plod:{name} a schema:GovernmentOrganization ;\n'
    base += f'    schema:location "gnjp:{name}" .\n'
    base += "\n"
    return base

def add_turtle_place(base, name):
    base += f'<http://geonames.jp/resource/{name}> a schema:Place ;\n'
    base += f'    rdfs:label "{name}" .\n'
    base += "\n"
    return base

def cv_publisher(a):
    if a == "厚労省":
        name = f"plod:厚生労働省"
    else:
        name = f"plod:{a}"
    postfix_publisher.setdefault(a, True)  # use it later.
    return name

def cv_location(a):
    name = f"gnjp:{a}"
    postfix_geoname.setdefault(a, True)  # use it later.
    return name

def cv_healthCondition(a):
    db = {
        "COVID-2019": "https://plod.info/rdf/COVID-19"
    }
    return finddb(db, a)

def make_date_time(obj, date_str, time_str):
    if obj.get(date_str):
        if obj.get(time_str):
            return f"{obj[date_str]}T{obj[time_str]}"
        else:
            return f"{obj[date_str]}"
    else:
        return None

#
# main
#
def plod_json2turtle(plod_list):
    """
    plod_list: json-like list of one or more dict.
    """
    rdf = __prefix
    # adding one or more PLOD in turtle.
    for jd in plod_list:
        reportId = jd["reportId"]
        publisher = cv_location(jd["publisher"])
        healthCondition = cv_healthCondition(jd["disease"])
        dateConfirmed = jd["dateConfirmed"]
        age = jd["age"]
        gender = jd["gender"]
        residence = cv_location(jd["residence"])
        patient_path = f"{reportId}-P01"

        rdf += "\n"
        rdf += f'''\
<{url_prefix}/{reportId}> a schema:Event ;
    rdfs:label "{reportId}" .

<{url_prefix}/{reportId}-R01> a schema:Report ;
    rdfs:label "{reportId}-R01" ;
    schema:mainEntity <{url_prefix}/{reportId}> ;
    plod:numberOfPatients "1"^^xsd:integer ;
    schema:datePublished "{dateConfirmed}"^^xsd:dateTime ;
    schema:publisher {publisher} ;
    schema:url <{report_url}> ;
    dcterms:isReferencedBy <{referencedBy}>.

<{url_prefix}/{patient_path}> a schema:Patient ;
    rdfs:label "{patient_path}" ;
    schema:subjectOf <{url_prefix}/{reportId}> ;
    schema:healthCondition <{healthCondition}> ;
    plod:dateConfirmed "{dateConfirmed}"^^xsd:dateTime ;
    foaf:age "{age}" ;
    schema:gender "{gender}" ;
    schema:homeLocation {residence} .
    '''

        rdf += "\n"
        labelMoveAction = 0;
        for x in jd["locationHistory"]:
            labelMoveAction += 1;
            agent_path = f"{patient_path}-M{labelMoveAction:02d}"
            rdf += f'<{url_prefix}/{agent_path}> a schema:MoveAction ;\n'
            rdf += f'    rdfs:label "{agent_path}" ;\n'
            rdf += f'    schema:agent <{url_prefix}/{patient_path}> ;\n'

            dt_str = make_date_time(x, "departureDate", "departureTime")
            if dt_str is not None:
                rdf += ('    schema:startTime "{}"^^xsd:dateTime ;\n'
                        .format(dt_str))

            if x.get("departureFrom"):
                rdf += ('    schema:fromLocation {} ;\n'
                        .format(cv_location(x["departureFrom"])))

            dt_str = make_date_time(x, "arrivalDate", "arrivalTime")
            if dt_str is not None:
                rdf += ('    schema:endTime "{}"^^xsd:dateTime ;\n'
                        .format(dt_str))

            if x.get("arrivalIn"):
                rdf += ('    schema:toLocation {} ;\n'
                        .format(cv_location(x["arrivalIn"])))

            if x.get("vehicles"):
                for v in x["vehicles"]:
                    rdf += (f'    schema:instrument "{v}"@ja .\n')
            rdf += "\n"

        # Publisher
        for k in postfix_publisher.keys():
            rdf = add_turtle_place(rdf, k)

        # Place
        for k in postfix_geoname.keys():
            rdf = add_turtle_place(rdf, k)

        # InfectiousDisease
        rdf += postfix
        rdf += "\n"

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
    turtle = plod_json2turtle(jd)
    print(turtle)
