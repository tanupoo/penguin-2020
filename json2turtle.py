import sys
import re
import json
import nta_conum_dict

#
# XXX TO BE DEFINED
#
referencedBy = "http://www.pref.TO_BE_DEFINED.lg.jp/shippei/kansenshou/keihatu-index.html"

#
# by definition
#
prefix_plod = "plod:"
prefix_dict = {
        "rdf:": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "rdfs:": "<http://www.w3.org/2000/01/rdf-schema#>",
        "xsd:": "<http://www.w3.org/2001/XMLSchema#>",
        "schema:": "<http://schema.org/>",
        "dcterms:": "<http://purl.org/dc/terms/>",
        "foaf:": "<http://xmlns.com/foaf/0.1/>",
        "gnjp:": "<http://geonames.jp/resource/>",
        prefix_plod: "<http://plod.info/rdf/>",
        }

"""
http://geonames.jp/resource
http://geonames.jp
"""

__postfix = f"""\
{prefix_plod}:COVID-19 a schema:InfectiousDisease ;
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

#
# add triple for the tale.
#
def add_turtle_publisher(key, prefix):
    conum = finddb(nta_conum_dict.co_num_dict, key)
    return "\n".join([
            f'{prefix_plod}{key} a schema:GovernmentOrganization ;',
            f'    schema:location "gnjp:{key}" ;',
            f'    rdfs:seeAlso <http://hojin-info.go.jp/data/basic/{conum}> .',
            ""])

def add_turtle_location(key, prefix):
    # f'<http://geonames.jp/resource/{a}> a schema:Place ;\n'
    return "\n".join([
            f'{prefix}:{key} a schema:Place ;',
            f'    rdfs:label "{prefix}{key}" .',
            ""])

#
# converting value.
#
def cv_publisher(a):
    if a == "厚労省":
        a = "厚生労働省"
    prefix = prefix_plod
    name = f"{prefix}{a}"
    postfix_publisher.setdefault(a, prefix)  # use it later.
    return name

def cv_location(a):
    prefix = "gnjp"
    name = f"{prefix}:{a}"
    postfix_geoname.setdefault(a, prefix)  # use it later.
    return name

def cv_healthCondition(a):
    db = {
        "COVID-2019": f"{prefix_plod}COVID-19"
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
    buf = []
    for k,v in prefix_dict.items():
        buf.append(f"@prefix {k} {v} .")
    buf.append("")  # for a line separator.
    #
    # adding one or more PLOD in turtle.
    for jd in plod_list:
        report_url = jd["dataSource"]
        reportId = jd["reportId"]
        publisher = cv_publisher(jd["publisher"])
        healthCondition = cv_healthCondition(jd["disease"])
        dateConfirmed = jd["dateConfirmed"]
        age = jd["age"]
        gender = jd["gender"]
        residence = cv_location(jd["residence"])
        patient_path = f"{reportId}-P01"

        buf.append(f'''\
{prefix_plod}{reportId} a schema:Event ;
    rdfs:label "{reportId}" .

{prefix_plod}{reportId}-R01 a schema:Report ;
    rdfs:label "{reportId}-R01" ;
    schema:mainEntity {prefix_plod}{reportId} ;
    {prefix_plod}numberOfPatients "1"^^xsd:integer ;
    schema:datePublished "{dateConfirmed}"^^xsd:dateTime ;
    schema:publisher {publisher} ;
    schema:url <{report_url}> ;
    dcterms:isReferencedBy <{referencedBy}>.

{prefix_plod}{patient_path} a schema:Patient ;
    rdfs:label "{patient_path}" ;
    schema:subjectOf {prefix_plod}{reportId} ;
    schema:healthCondition <{healthCondition}> ;
    {prefix_plod}dateConfirmed "{dateConfirmed}"^^xsd:dateTime ;
    foaf:age "{age}" ;
    schema:gender "{gender}" ;
    schema:homeLocation {residence} .
''')
        # adding locations
        labelMoveAction = 0;
        for x in jd["locationHistory"]:
            labelMoveAction += 1;
            agent_path = f"{patient_path}-M{labelMoveAction:02d}"
            buf.append(f'{prefix_plod}{agent_path} a schema:MoveAction ;')
            buf.append(f'    rdfs:label "{agent_path}" ;')
            buf.append(f'    schema:agent {prefix_plod}{patient_path} ;')

            dt_str = make_date_time(x, "departureDate", "departureTime")
            if dt_str is not None:
                buf.append(('    schema:startTime "{}"^^xsd:dateTime ;'
                            .format(dt_str)))

            if x.get("departureFrom"):
                buf.append('    schema:fromLocation {} ;'
                           .format(cv_location(x["departureFrom"])))

            dt_str = make_date_time(x, "arrivalDate", "arrivalTime")
            if dt_str is not None:
                buf.append('    schema:endTime "{}"^^xsd:dateTime ;'
                           .format(dt_str))

            if x.get("arrivalIn"):
                buf.append('    schema:toLocation {} ;'
                           .format(cv_location(x["arrivalIn"])))

            if x.get("vehicles"):
                for v in x["vehicles"]:
                    buf.append(f'    schema:instrument "{v}"@ja ;')

            # replace the end of char in the end of line into ".".
            buf[-1] = buf[-1][:-1] + "."

            buf.append("")  # for a line separator.

        # Place
        for key,prefix in postfix_geoname.items():
            buf.append(add_turtle_location(key, prefix))

        # Publisher
        for key,prefix in postfix_publisher.items():
            buf.append(add_turtle_publisher(key, prefix))

        # InfectiousDisease
        buf.append(__postfix)

        buf.append("")  # for a line separator.

    return "\n".join(buf)
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
