# These tests are taken from SPARQLWrapper's public endpoint tests,
# https://github.com/RDFLib/sparqlwrapper/blob/master/test/test_public_endpoints.py, to ensure that kurra can do what
# SPARQLWrapper does
#
# The results of these tests aren't required all to be pass but required to match or better SPARQLWrapper
#
# 2026-07-15: SPARQLWrapper on test_pubic_endpoints.py: 77 failed, 504 passed, 267 skipped, 199 warnings in 1069.45s (0:17:49)

import pytest
from kurra.sparql import query

_SPARQL_DEFAULT = ["application/sparql-results+xml", "application/rdf+xml", "*/*"]
_SPARQL_XML = ["application/sparql-results+xml"]
_SPARQL_JSON = [
    "application/x-sparqlstar-results+json", # prevents serialization of quoted/embedded triples in GraphDB, see https://graphdb.ontotext.com/documentation/10.7/rdf-sparql-star.html
    "application/sparql-results+json",
    "application/json",
    "text/javascript",
    "application/javascript",
]  # VIVO server returns "application/javascript"
_RDF_XML = ["application/rdf+xml"]
_RDF_TURTLE = ["application/turtle", "text/turtle"]
_RDF_N3 = _RDF_TURTLE + [
    "text/rdf+n3",
    "application/n-triples",
    "application/n3",
    "text/n3",
]
_RDF_JSONLD = ["application/ld+json", "application/x-json+ld"]
_CSV = ["text/csv"]
_TSV = ["text/tab-separated-values"]
_XML = ["application/xml"]
_ALL = ["*/*"]

_RDF_POSSIBLE = _RDF_XML + _RDF_N3 + _XML + _RDF_JSONLD
_SPARQL_SELECT_ASK_POSSIBLE = _SPARQL_XML + _SPARQL_JSON + _CSV + _TSV + _XML
_SPARQL_DESCRIBE_CONSTRUCT_POSSIBLE = _RDF_XML + _RDF_N3 + _XML + _RDF_JSONLD

VIRTUOSO_8_03_3334_dbpedia = "https://dbpedia.org/sparql"
BLAZEGRAPH_WIKIDATA = "https://query.wikidata.org/sparql"
RDF4J_GEOSCIML = "http://vocabs.ands.org.au/repository/api/sparql/csiro_international-chronostratigraphic-chart_2018-revised-corrected"
ALLEGROGRAPH_AGROVOC = "https://agrovoc.fao.org/sparql"
ALLEGROGRAPH_4_14_1_MMI = "https://mmisw.org/sparql"  # AllegroServe/1.3.28 http://mmisw.org:10035/doc/release-notes.html
FUSEKI_LOV = "https://lov.linkeddata.es/dataset/lov/sparql"  # Fuseki - version 1.1.1 (Build date: 2014-10-02T16:36:17+0100)
STARDOG_LINDAS = "https://lindas.admin.ch/query"  # human UI https://lindas.admin.ch/sparql/
STORE4_1_1_4_CHISE = "http://rdf.chise.org/sparql"  # 4store SPARQL server v1.1.4

# Test parameters
@pytest.fixture(params=[
    VIRTUOSO_8_03_3334_dbpedia,
    BLAZEGRAPH_WIKIDATA,
    RDF4J_GEOSCIML,
    ALLEGROGRAPH_AGROVOC,
    ALLEGROGRAPH_4_14_1_MMI,
    FUSEKI_LOV,
    STARDOG_LINDAS,
    STORE4_1_1_4_CHISE
])
def endpoint(request):
    return request.param

@pytest.fixture
def endpoint_config(endpoint):
    """Provide endpoint-specific configurations (prefixes and queries)"""
    if endpoint == ALLEGROGRAPH_AGROVOC:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
""",
            "select_query": """
    SELECT ?label
    WHERE {
    <http://aims.fao.org/aos/agrovoc/c_aca7ac6d> skos:prefLabel ?label .
    }
""",
            "select_query_csv_tsv": """
    SELECT ?label ?created
    WHERE {
    <http://aims.fao.org/aos/agrovoc/c_aca7ac6d> skos:prefLabel ?label ;
        <http://purl.org/dc/terms/created> ?created
    }
""",
            "ask_query": """
    ASK { <http://aims.fao.org/aos/agrovoc/c_aca7ac6d> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://aims.fao.org/aos/agrovoc/c_aca7ac6d> skos:prefLabel ?label .
    }
""",
            "describe_query": """
    DESCRIBE <http://aims.fao.org/aos/agrovoc/c_aca7ac6d>
"""
        }

    elif endpoint == ALLEGROGRAPH_4_14_1_MMI:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX ioosCat: <http://mmisw.org/ont/ioos/category/>
    PREFIX ioosPlat: <http://mmisw.org/ont/ioos/platform/>
""",
            "select_query": """
    SELECT ?p
    WHERE { ?p a ioosCat:Category }
    ORDER BY ?p
""",
            "select_query_csv_tsv": """
    SELECT DISTINCT ?cat ?platform ?definition
    WHERE {
        ?platform a ioosPlat:Platform .
        ?platform ioosPlat:Definition ?definition .
        ?cat skos:narrowMatch ?platform .
    }
    ORDER BY ?cat ?platform
""",
            "ask_query": """
    ASK { <http://mmisw.org/ont/ioos/platform/aircraft> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://mmisw.org/ont/ioos/platform/aircraft> rdfs:label ?label .
    }
""",
            "describe_query": """
    DESCRIBE <http://mmisw.org/ont/ioos/platform/aircraft>
"""
        }

    elif endpoint == BLAZEGRAPH_WIKIDATA:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX entity: <http://www.wikidata.org/entity/>
""",
            "select_query": """
    SELECT ?predicate ?object WHERE {
        entity:Q3934 ?predicate ?object .
    } LIMIT 10
""",
            "select_query_csv_tsv": """
    SELECT ?predicate ?object WHERE {
        entity:Q3934 ?predicate ?object .
    } LIMIT 10
""",
            "ask_query": """
    ASK { <http://www.wikidata.org/entity/Q3934> rdfs:label "Asturias"@es }
""",
            "construct_query": """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://www.wikidata.org/entity/Q3934> rdfs:label ?label .
        FILTER langMatches( lang(?label), "es" )
    }
""",
            "describe_query": """
    DESCRIBE <http://www.wikidata.org/entity/Q3934>
"""
        }

    elif endpoint == FUSEKI_LOV:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX lov: <http://lov.linkeddata.es/dataset/lov/>
""",
            "select_query": """
    SELECT ?subject ?predicate ?object WHERE {
        ?subject ?predicate ?object .
    } LIMIT 10
""",
            "select_query_csv_tsv": """
    SELECT ?subject ?predicate ?object WHERE {
        ?subject ?predicate ?object .
    } LIMIT 10
""",
            "ask_query": """
    ASK { <http://lov.linkeddata.es/dataset/lov/vocabulary> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://lov.linkeddata.es/dataset/lov/vocabulary> rdfs:label ?label .
    }
""",
            "describe_query": """
    DESCRIBE <http://lov.linkeddata.es/dataset/lov/vocabulary>
"""
        }

    elif endpoint == RDF4J_GEOSCIML:
        return {
            "prefixes": """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
""",
            "select_query": """
    SELECT DISTINCT ?era ?label ?notation
    {
        ?era a <http://resource.geosciml.org/ontology/timescale/gts#GeochronologicEra> ;
        rdfs:label ?label ;
        skos:notation ?notation .
    } LIMIT 100
""",
            "select_query_csv_tsv": """
    SELECT DISTINCT ?era ?label ?notation
    {
        ?era a <http://resource.geosciml.org/ontology/timescale/gts#GeochronologicEra> ;
        rdfs:label ?label ;
        skos:notation ?notation .
    } LIMIT 100
""",
            "ask_query": """
    ASK { <http://resource.geosciml.org/classifier/ics/ischart/Jurassic> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v rdfs:label ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://resource.geosciml.org/classifier/ics/ischart/Jurassic> rdfs:label ?label .
    }
""",
            "describe_query": """
    DESCRIBE <http://resource.geosciml.org/classifier/ics/ischart/Jurassic>
"""
        }

    elif endpoint == STARDOG_LINDAS:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX lindas: <https://lindas.admin.ch/>
""",
            "select_query": """
    SELECT ?subject ?predicate ?object WHERE {
        ?subject ?predicate ?object .
    } LIMIT 10
""",
            "select_query_csv_tsv": """
    SELECT ?subject ?predicate ?object WHERE {
        ?subject ?predicate ?object .
    } LIMIT 10
""",
            "ask_query": """
    ASK { <https://lindas.admin.ch/resource/Example> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v skos:prefLabel ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <https://lindas.admin.ch/resource/Example> rdfs:label ?label .
    }
""",
            "describe_query": """
    DESCRIBE <https://lindas.admin.ch/resource/Example>
"""
        }

    elif endpoint == STORE4_1_1_4_CHISE:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
""",
            "select_query": """
    SELECT DISTINCT ?s WHERE {
         ?s a ?o .
    } LIMIT 100
""",
            "select_query_csv_tsv": """
    SELECT DISTINCT ?s ?o WHERE {
        ?s a ?o .
    } LIMIT 100
""",
            "ask_query": """
    ASK {
        ?type a <http://rdf.chise.org/rdf/type/character/ggg/super-abstract-character> .
    }
""",
            "construct_query": """
    CONSTRUCT {
        _:v rdfs:type ?type .
        _:v rdfs:comment "this is only a mock node to test library" .
    }
    WHERE {
        <http://www.chise.org/est/view/character/a2.ucs@bucs=0x5C08> rdfs:type ?type .
    }
""",
            "describe_query": """
    DESCRIBE <http://www.chise.org/est/view/character/a2.ucs@bucs=0x5C08>
"""
        }

    else:
        return {
            "prefixes": """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
""",
            "select_query": """
    SELECT ?label
    WHERE {
    <http://dbpedia.org/resource/Asturias> rdfs:label ?label .
    }
""",
            "select_query_csv_tsv": """
    SELECT ?label ?wikiPageID
    WHERE {
    <http://dbpedia.org/resource/Asturias> rdfs:label ?label ;
        <http://dbpedia.org/ontology/wikiPageID> ?wikiPageID
    }
""",
            "ask_query": """
    ASK { <http://dbpedia.org/resource/Asturias> a ?type }
""",
            "construct_query": """
    CONSTRUCT {
        _:v rdfs:label ?label .
        _:v rdfs:comment "this is only a mock node to test library"
    }
    WHERE {
        <http://dbpedia.org/resource/Asturias> rdfs:label ?label .
    }
""",
            "describe_query": """
    DESCRIBE <http://dbpedia.org/resource/Asturias>
"""
        }

@pytest.fixture
def prefixes(endpoint_config):
    return endpoint_config["prefixes"]

@pytest.fixture
def select_query(endpoint_config):
    return endpoint_config["select_query"]

@pytest.fixture
def select_query_csv_tsv(endpoint_config):
    return endpoint_config["select_query_csv_tsv"]

@pytest.fixture
def ask_query(endpoint_config):
    return endpoint_config["ask_query"]

@pytest.fixture
def construct_query(endpoint_config):
    return endpoint_config["construct_query"]

@pytest.fixture
def describe_query(endpoint_config):
    return endpoint_config["describe_query"]


