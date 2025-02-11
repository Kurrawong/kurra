from io import StringIO
from pathlib import Path

from rdflib import RDF, Graph, URIRef

from kurra.db import create_dataset, list_dataset


def test_db_create_dataset_by_dataset_name(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "myds"
    return_value = create_dataset(base_url, dataset_name, http_client=http_client)
    assert return_value == f"Dataset {dataset_name} created at {base_url}."

    result = list_dataset(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))


def test_db_create_dataset_by_config_file(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "myds"
    config_file = StringIO(
        """PREFIX :          <http://base/#>
PREFIX bibo:      <http://purl.org/ontology/bibo/>
PREFIX dc:        <http://purl.org/dc/elements/1.1/>
PREFIX dcterms:   <http://purl.org/dc/terms/>
PREFIX ex:        <http://example.org/>
PREFIX fuseki:    <http://jena.apache.org/fuseki#>
PREFIX geosparql: <http://jena.apache.org/geosparql#>
PREFIX rdf:       <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:      <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema:    <https://schema.org/>
PREFIX skos:      <http://www.w3.org/2004/02/skos/core#>
PREFIX tdb2:      <http://jena.apache.org/2016/tdb#>
PREFIX text:      <http://jena.apache.org/text#>

:service_tdb_all  rdf:type  fuseki:Service;
        rdfs:label       "myds";
        fuseki:dataset   :geosparql_dataset;
        fuseki:endpoint  [ fuseki:name       "query";
                           fuseki:operation  fuseki:query
                         ];
        fuseki:endpoint  [ fuseki:name       "data";
                           fuseki:operation  fuseki:gsp-rw
                         ];
        fuseki:endpoint  [ fuseki:name       "get";
                           fuseki:operation  fuseki:gsp-r
                         ];
        fuseki:endpoint  [ fuseki:operation  fuseki:update ];
        fuseki:endpoint  [ fuseki:operation  fuseki:gsp-rw ];
        fuseki:endpoint  [ fuseki:name       "sparql";
                           fuseki:operation  fuseki:query
                         ];
        fuseki:endpoint  [ fuseki:operation  fuseki:query ];
        fuseki:endpoint  [ fuseki:name       "update";
                           fuseki:operation  fuseki:update
                         ];
        fuseki:name      "myds" .

:geosparql_dataset  rdf:type            geosparql:geosparqlDataset;
        geosparql:applyDefaultGeometry  false;
        geosparql:dataset               :text_dataset;
        geosparql:indexEnabled          true;
        geosparql:indexExpires          "5000,5000,5000";
        geosparql:indexSizes            "-1,-1,-1";
        geosparql:inference             false;
        geosparql:queryRewrite          true;
        geosparql:spatialIndexFile      "/fuseki/databases/myds/spatial.index" .

:text_dataset  rdf:type  text:TextDataset;
        text:dataset  :tdb_dataset_readwrite;
        text:index    :index_lucene .

:tdb_dataset_readwrite
        rdf:type                tdb2:DatasetTDB2;
        tdb2:location           "/fuseki/databases/myds";
        tdb2:unionDefaultGraph  true .

:index_lucene  rdf:type   text:TextIndexLucene;
        text:analyzer     [ rdf:type  text:StandardAnalyzer ];
        text:directory    "/fuseki/databases/myds";
        text:entityMap    :entity_map;
        text:propLists    ( [ text:propListProp  ex:searchFields;
                              text:props         ( schema:headline schema:name bibo:shortTitle dcterms:title dc:title bibo:abstract schema:description dc:description dcterms:description rdfs:label skos:prefLabel skos:altLabel )
                            ]
                          );
        text:storeValues  true .

:entity_map  rdf:type      text:EntityMap;
        text:defaultField  "prefLabel";
        text:entityField   "uri";
        text:graphField    "graph";
        text:langField     "lang";
        text:map           ( [ text:field      "prefLabel";
                               text:predicate  skos:prefLabel
                             ]
                             [ text:field      "altLabel";
                               text:predicate  skos:altLabel
                             ]
                             [ text:field      "notation";
                               text:predicate  skos:notation
                             ]
                             [ text:field      "definition";
                               text:predicate  skos:definition
                             ]
                             [ text:field      "hidden";
                               text:predicate  skos:hiddenLabel
                             ]
                             [ text:field      "rdfslabel";
                               text:predicate  rdfs:label
                             ]
                             [ text:field      "headline";
                               text:predicate  schema:headline
                             ]
                             [ text:field      "name";
                               text:predicate  schema:name
                             ]
                             [ text:field      "shortTitle";
                               text:predicate  bibo:shortTitle
                             ]
                             [ text:field      "dcttitle";
                               text:predicate  dcterms:title
                             ]
                             [ text:field      "dctitle";
                               text:predicate  dc:title
                             ]
                             [ text:field      "abstract";
                               text:predicate  bibo:abstract
                             ]
                             [ text:field      "sdodescription";
                               text:predicate  schema:description
                             ]
                             [ text:field      "dctdescription";
                               text:predicate  dcterms:description
                             ]
                             [ text:field      "dcdescription";
                               text:predicate  dc:description
                             ]
                           );
        text:uidField      "uid" ."""
    )
    return_value = create_dataset(base_url, config_file, http_client=http_client)
    assert (
        return_value
        == f"Dataset {dataset_name} created using assembler config at {base_url}."
    )

    result = list_dataset(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))


def test_db_create_dataset_by_config_file_with_existing_dataset(
    fuseki_container, http_client
):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    current_dir = Path(__file__).parent
    file = current_dir / "config.ttl"
    graph = Graph().parse(file, format="turtle")
    fuseki_service = graph.value(
        None, RDF.type, URIRef("http://jena.apache.org/fuseki#Service")
    )
    dataset_name = graph.value(
        fuseki_service, URIRef("http://jena.apache.org/fuseki#name")
    )
    return_value = create_dataset(base_url, file, http_client=http_client)

    assert (
        return_value
        == f"Dataset {dataset_name} created using assembler config at {base_url}."
    )

    result = list_dataset(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))
