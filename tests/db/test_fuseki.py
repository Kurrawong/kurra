import json
from datetime import datetime
from io import StringIO
from pathlib import Path

import pytest
from rdflib import RDF, Graph, URIRef

from kurra.db.fuseki import (
    FusekiError,
    backup,
    backups,
    backups_list,
    create,
    delete,
    describe,
    metrics,
    ping,
    server,
    sleep,
    stats,
    status,
    tasks,
)
from kurra.sparql import query


def test_ping(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = ping(server_url, http_client=http_client)
    assert r.startswith(str(datetime.now().year))


def test_server(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = server(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"][0]["ds.name"] == "/ds"


def test_status(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = status(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"][0]["ds.name"] == "/ds"


def test_stats(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    # bump Request up by 2
    query(server_url + "/ds", "ASK WHERE {?s ?p ?o}", http_client=http_client)
    query(server_url + "/ds", "ASK WHERE {?s ?p ?o}", http_client=http_client)

    r = stats(server_url, None, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"]["/ds"]["Requests"] == 2

    # adding in the name of an existing dataset gets the same result as no name
    # adding in a non-existent name gets a 404 and no result
    r = stats(server_url, "ds", http_client=http_client)
    j = json.loads(r)
    assert j["datasets"]["/ds"]["Requests"] == 2


def test_backup(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    with pytest.raises(NotImplementedError) as e:
        backup(server_url, None, http_client=http_client)

        assert str(e) == "backup/backups is not implemented yet"


def test_backups(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    with pytest.raises(NotImplementedError) as e:
        backups(server_url, None, http_client=http_client)

        assert str(e) == "backup/backups is not implemented yet"


def test_backups_list(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = backups_list(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["backups"] == []


def test_sleep(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    with pytest.raises(NotImplementedError) as e:
        sleep(server_url, http_client=http_client)

        assert str(e) == "sleep is not implemented yet"


def test_tasks(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = tasks(server_url, None, http_client=http_client)
    j = json.loads(r)
    assert j == []


def test_metrics(fuseki_container, http_client):
    server_url = f"http://localhost:{fuseki_container.get_exposed_port(3030)}"

    r = metrics(server_url, http_client=http_client)
    assert "# HELP" in r


def test_describe(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    r = describe(base_url, http_client=http_client)
    assert "/ds" in list(map(lambda x: x["ds.name"], r))


def test_describe_one(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    r = describe(base_url, "ds", http_client=http_client)
    assert r["ds.name"] == "/ds"


def test_describe_non_existent(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}/some-url"
    with pytest.raises(FusekiError) as exc_info:
        describe(base_url, http_client)

    assert (
        f"Failed to list datasets at http://localhost:{port}/some-url"
        in exc_info.value.message
    )


def test_create_by_dataset_name(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "myds"
    r = create(base_url, dataset_name, http_client=http_client)
    assert r == f"Dataset {dataset_name} created at {base_url}."

    result = describe(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))


def test_create_by_config_file(fuseki_container, http_client):
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
    r = create(base_url, config_file, http_client=http_client)
    assert r == f"Dataset {dataset_name} created using assembler config at {base_url}."

    result = describe(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))


def test_create_by_config_file_with_existing_dataset(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    file = Path(__file__).parent.parent / "cli/db/config.ttl"
    graph = Graph().parse(file, format="turtle")
    fuseki_service = graph.value(
        None, RDF.type, URIRef("http://jena.apache.org/fuseki#Service")
    )
    dataset_name = graph.value(
        fuseki_service, URIRef("http://jena.apache.org/fuseki#name")
    )
    r = create(base_url, file, http_client=http_client)

    assert r == f"Dataset {dataset_name} created using assembler config at {base_url}."

    result = describe(base_url, http_client=http_client)
    assert f"/{dataset_name}" in list(map(lambda x: x["ds.name"], result))


def test_delete(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "ds"
    r = delete(base_url, dataset_name, http_client)
    assert r == f"Dataset {dataset_name} deleted."


def test_delete_non_existent(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    base_url = f"http://localhost:{port}"
    dataset_name = "non-existent"

    with pytest.raises(FusekiError) as exc_info:
        delete(base_url, dataset_name, http_client)

    assert f"Failed to delete dataset '{dataset_name}'" in exc_info.value.message
