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
#     NOTE: prefix must include a colon at the end.
#
prefix_geoname = "gnjp:"
prefix_plod = "plod:"
prefix_dict = {
        "rdf:": "<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "rdfs:": "<http://www.w3.org/2000/01/rdf-schema#>",
        "xsd:": "<http://www.w3.org/2001/XMLSchema#>",
        "schema:": "<http://schema.org/>",
        "dcterms:": "<http://purl.org/dc/terms/>",
        "foaf:": "<http://xmlns.com/foaf/0.1/>",
        prefix_geoname: "<http://geonames.jp/resource/>",
        prefix_plod: "<http://plod.info/rdf/>",
        }

#
#
#
__postfix = f"""\
<http://purl.bioontology.org/ontology/ICD10/U07.1> a schema:MedicalCode ;
    schema:codeValue "U07.1" ;
    schema:codingSystem "ICD-10" .
"""

#
#
#
postfix_geoname = {}
postfix_publisher = {}
postfix_disease = {}

def finddb(db, search_key):
    v = [ x[1] for x in nta_conum_dict.co_num_dict.items() if x[0] == search_key ]
    if len(v):
        return v[0]
    return None

#
# add triple for the tale.
#
def get_iri(key, prefix):
    return f'{prefix}{key}' if (prefix is not None and len(prefix) > 0) else f'<{key}>'

def add_turtle_publisher(key, prefix):
    conum = finddb(nta_conum_dict.co_num_dict, key)
    return "\n".join([
            f'{get_iri(key, prefix)} a schema:GovernmentOrganization ;',
            f'    schema:location "gnjp:{key}" ;',
            f'    rdfs:seeAlso <http://hojin-info.go.jp/data/basic/{conum}> .',
            ""])

def add_turtle_location(key, prefix):
    return "\n".join([
            f'{get_iri(key, prefix)} a schema:Place ;',
            f'    rdfs:label "{prefix}{key}" .',
            ""])

def add_turtle_webpage(key, prefix):
    return "\n".join([
            f'{get_iri(key, prefix)} a schema:WebPage .',
            ""])

def add_turtle_disease(key, prefix):
    # XXX need to check if key is "COVID-19"
    return "\n".join([
            f'{get_iri(key, prefix)} a schema:InfectiousDisease ;',
            f'    rdfs:label "COVID-19" ;',
            f'    schema:name "2019-nCoV acute respiratory disease"@en ;',
            f'    schema:infectiousAgent "2019-nCoV" ;',
            f'    schema:code <http://purl.bioontology.org/ontology/ICD10/U07.1> .',
            ""])

#
# converting value.
#
def cv_publisher(a):
    if a == "厚労省":
        a = "厚生労働省"
    postfix_publisher.setdefault(a, prefix_plod)  # use it later.
    return f"{prefix_plod}{a}"

def cv_location(a):
    postfix_geoname.setdefault(a, prefix_geoname)  # use it later.
    return f"{prefix_geoname}{a}"

def cv_healthCondition(a):
    if a == "COVID-2019":
        a = "COVID-19"
    postfix_disease.setdefault(a, prefix_plod)  # use it later.
    return f"{prefix_plod}{a}"

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
        o_healthCondition = cv_healthCondition(jd["disease"])
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
    dcterms:isReferencedBy <{referencedBy}> .

{prefix_plod}{patient_path} a schema:Patient ;
    rdfs:label "{patient_path}" ;
    schema:subjectOf {prefix_plod}{reportId} ;
    schema:healthCondition {o_healthCondition} ;
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
        add_x(buf, postfix_geoname, add_turtle_location)

        # Publisher
        add_x(buf, postfix_publisher, add_turtle_publisher)

        # WebPage
        add_x(buf, { report_url: "", referencedBy: "" }, add_turtle_webpage)

        # Disease
        add_x(buf, postfix_disease, add_turtle_disease)

        # InfectiousDisease
        buf.append(__postfix)

        buf.append("")  # for a line separator.

    return "\n".join(buf)

def add_x(buf, subject_list, func):
    for key,prefix in subject_list.items():
        buf.append(func(key, prefix))

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
