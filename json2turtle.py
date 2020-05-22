import sys
import re
import json
import nta_conum_dict

#
# XXX TO BE DEFINED
#
referencedBy = "http://www.TO_BE_DEFINED.lg.jp/"

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
# add triple for the tale.
#
def get_v(db, search_key):
    v = [ x[1] for x in db.items() if x[0] == search_key ]
    if len(v):
        return v[0]
    return None

class t3_maker:
    def __init__(self):
        self.refs = {}

    def append(self, name, prefix=None):
        self.refs.setdefault(name, prefix)

    def get_iri(self, key, prefix):
        return f'{prefix}{key}' if (prefix is not None and len(prefix) > 0) else f'<{key}>'

class t3_webpage(t3_maker):
    def finalize(self, buf):
        for key,prefix in self.refs.items():
            buf.append("\n".join([
                f'{self.get_iri(key, prefix)} a schema:WebPage .',
                ""]))

class t3_place(t3_maker):
    def finalize(self, buf):
        for key,prefix in self.refs.items():
            buf.append("\n".join([
                    f'{self.get_iri(key, prefix)} a schema:Place ;',
                    f'    rdfs:label "{prefix}{key}" .',
                    ""]))

class t3_publisher(t3_maker):
    def finalize(self, buf):
        t3_list = []
        for key,prefix in self.refs.items():
            conum = get_v(nta_conum_dict.co_num_dict, key)
            t3_list.append(f'{self.get_iri(key, prefix)} a schema:GovernmentOrganization')
            t3_list.append(f'    schema:location "gnjp:{key}"')
            t3_list.append(f'    rdfs:seeAlso <http://hojin-info.go.jp/data/basic/{conum}>')
            t3_list[-1] += " .\n"
            buf.append(" ;\n".join(t3_list))

class t3_disease(t3_maker):
    def finalize(self, buf):
        t3_list = []
        for key,prefix in self.refs.items():
            # XXX need to check if key is "COVID-19"
            t3_list.append(f'{self.get_iri(key, prefix)} a schema:InfectiousDisease')
            t3_list.append(f'    rdfs:label "COVID-19"')
            t3_list.append(f'    schema:name "2019-nCoV acute respiratory disease"@en')
            t3_list.append(f'    schema:infectiousAgent "2019-nCoV"')
            t3_list.append(f'    schema:code <http://purl.bioontology.org/ontology/ICD10/U07.1>')
            t3_list[-1] += " .\n"
            buf.append(" ;\n".join(t3_list))

t3x_disease = t3_disease()
t3x_publisher = t3_publisher()
t3x_place = t3_place()
t3x_webpage = t3_webpage()

#
# converting value.
#
def cv_publisher(a):
    if a == "厚労省":
        a = "厚生労働省"
    t3x_publisher.append(a, prefix_plod)  # use it later.
    return f"{prefix_plod}{a}"

def cv_location(a):
    t3x_place.append(a, prefix_geoname)
    return f"{prefix_geoname}{a}"

def cv_healthCondition(a):
    if a == "COVID-2019":
        a = "COVID-19"
    t3x_disease.append(a, prefix_plod)  # use it later.
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
        reportId = jd["reportId"]
        publisher = cv_publisher(jd["publisher"])
        o_healthCondition = cv_healthCondition(jd["disease"])
        dateConfirmed = jd["dateConfirmed"]
        age = jd["age"]
        gender = jd["gender"]
        residence = cv_location(jd["residence"])
        patient_path = f"{reportId}-P01"

        # schema:Event
        buf.append(f'''\
{prefix_plod}{reportId} a schema:Event ;
    rdfs:label "{reportId}" .
''')

        # schema:Report
        # XXX method 1
        t3_list = []
        t3_list.append(f'{prefix_plod}{reportId}-R01 a schema:Report')
        t3_list.append(f'    rdfs:label "{reportId}-R01"')
        t3_list.append(f'    schema:mainEntity {prefix_plod}{reportId}')
        t3_list.append(f'    {prefix_plod}numberOfPatients "1"^^xsd:integer')
        t3_list.append(f'    schema:datePublished "{dateConfirmed}"^^xsd:dateTime')
        t3_list.append(f'    schema:publisher {publisher}')
        report_url = jd.get("dataSource")
        if report_url is not None and len(report_url) > 0:
            t3_list.append(f'    schema:url <{report_url}>')
            t3x_webpage.append(report_url)
            t3_list.append(f'    dcterms:isReferencedBy <{referencedBy}>')
            t3x_webpage.append(referencedBy)
        t3_list[-1] += " .\n"
        buf.append(" ;\n".join(t3_list))

        # schema:Patient
        # XXX method 2
        t3_list = []
        t3_list.append(f'{prefix_plod}{patient_path} a schema:Patient')
        t3_list.append(f'    rdfs:label "{patient_path}"')
        t3_list.append(f'    schema:subjectOf {prefix_plod}{reportId}')
        t3_list.append(f'    schema:healthCondition {o_healthCondition}')
        t3_list.append(f'    {prefix_plod}dateConfirmed "{dateConfirmed}"^^xsd:dateTime')
        t3_list.append(f'    foaf:age "{age}"')
        t3_list.append(f'    schema:gender "{gender}"')
        t3_list.append(f'    schema:homeLocation {residence}')
        t3_list[-1] += " .\n"
        buf.append(" ;\n".join(t3_list))

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
        t3x_place.finalize(buf)

        # Publisher
        t3x_publisher.finalize(buf)

        # WebPage
        t3x_webpage.finalize(buf)

        # Disease
        t3x_disease.finalize(buf)

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
    if jd.get("plod"):
        jd = jd["plod"]
    turtle = plod_json2turtle(jd)
    print(turtle)
