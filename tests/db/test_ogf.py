import datetime
import time
from pathlib import Path
from textwrap import dedent

from rdflib import Dataset, URIRef
from rdflib.namespace import RDF, SDO

import kurra.utils
from kurra.db.ogf import OLIS, SYSTEM_GRAPH_IRI, exclude, include, validate_system_graph

this_dir = Path(__file__).resolve().parent

basic_vg = dedent(
    """
    PREFIX olis: <https://olis.dev/>
    PREFIX schema: <https://schema.org/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    
    <http://example.org/g/1>
        a olis:VirtualGraph ;
        olis:includes
            <http://background> ,
            <http://example.org/g/a> ,
            <http://example.org/g/b> ;
        schema:dateCreated "2026-01-01T17:25:32"^^xsd:dateTime ;
        schema:dateModified "2026-01-10T17:25:32"^^xsd:dateTime ;
    .    
    """
)

simple_rg_01 = dedent(
    """
    PREFIX ex: <http://example.com/>
    
    ex:a
        ex:b ex:c ;
        ex:d ex:e ;
    .
    """
)

simple_rg_02 = dedent(
    """
    PREFIX ex: <http://example.com/>

    ex:f
        ex:g ex:h ;
        ex:i ex:j ;
        ex:k ex:l ;
    .
    """
)

dataset_trig = dedent(
    """
PREFIX ex: <http://example.com/>
PREFIX olis: <https://olis.dev/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

<https://olis.dev/SystemGraph> {
    <http://example.org/g/1>
        a olis:VirtualGraph ;
        olis:includes
            <http://background> ,
            <http://example.org/g/a> ,
            <http://example.org/g/b> ;
        schema:dateCreated "2026-01-01T17:25:32"^^xsd:dateTime ;
        schema:dateModified "2026-01-10T17:25:32"^^xsd:dateTime ;
    .
}

<http://example.org/g/a> {
    ex:a
        ex:b ex:c ;
        ex:d ex:e ;
    .
}

<http://example.org/g/b> {
    ex:f
        ex:g ex:h ;
        ex:i ex:j ;
    .
}
    """
)


def test_include_none():
    including_graph_iri = URIRef("http://example.org/g/1")
    sg = include(
        including_graph_iri, ["http://example.org/g/x", "http://example.org/g/y"], None
    )

    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    assert (including_graph_iri, SDO.dateCreated, None) in sg


def test_include_nothing():
    remote_sg = this_dir / "ogf" / "01-add-to-nothing.ttl"
    including_graph_iri = URIRef("http://example.org/g/1")
    include(
        including_graph_iri,
        ["http://example.org/g/x", "http://example.org/g/y"],
        remote_sg,
    )

    sg = kurra.utils.load_graph(remote_sg)
    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    assert (including_graph_iri, SDO.dateCreated, None) in sg

    # reset test file
    with open(remote_sg, "w") as f:
        f.write("""PREFIX olis: <https://olis.dev/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>""")


def test_include_existing_vg():
    start_time = datetime.datetime.now()
    time.sleep(1)
    target_sg = this_dir / "ogf" / "02-add-to-vg.ttl"
    including_graph_iri = URIRef("http://example.org/g/1")
    include(
        including_graph_iri,
        ["http://example.org/g/x", "http://example.org/g/y"],
        target_sg,
    )

    sg = kurra.utils.load_graph(target_sg)
    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    dc = sg.value(subject=including_graph_iri, predicate=SDO.dateCreated)
    assert dc.value == datetime.datetime.strptime(
        "2026-01-01T17:25:32", "%Y-%m-%dT%H:%M:%S"
    )
    dm = sg.value(subject=including_graph_iri, predicate=SDO.dateModified)
    assert dm.value > start_time

    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/a")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/b")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/x")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/y")) in sg

    # reset test file
    with open(target_sg, "w") as f:
        f.write(basic_vg)


def test_include_convert_rg():
    target_sg = this_dir / "ogf" / "03-convert-rg.ttl"
    including_graph_iri = URIRef("http://example.org/g/1")
    new_rg_iri = URIRef(str(including_graph_iri) + "-real")
    include(
        including_graph_iri,
        ["http://example.org/g/x", "http://example.org/g/y"],
        target_sg,
    )

    sg = kurra.utils.load_graph(target_sg)
    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    assert (including_graph_iri, OLIS.includes, new_rg_iri) in sg
    assert (new_rg_iri, RDF.type, OLIS.RealGraph) in sg

    # reset test file
    with open(target_sg, "w") as f:
        f.write("""PREFIX olis: <https://olis.dev/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

<http://example.org/g/1>
    a olis:RealGraph ;
    schema:dateCreated "2026-01-01T17:25:32"^^xsd:dateTime ;
    schema:dateModified "2026-01-10T17:25:32"^^xsd:dateTime ;
.
    """)


def test_include_local_dataset():
    start_time = datetime.datetime.now()
    time.sleep(1)
    target_sg = this_dir / "ogf" / "04-local-dataset.trig"
    including_graph_iri = URIRef("http://example.org/g/1")
    include(
        including_graph_iri,
        ["http://example.org/g/x", "http://example.org/g/y"],
        target_sg,
    )

    local_dataset = Dataset().parse(target_sg, format="trig")
    sg = local_dataset.get_graph(SYSTEM_GRAPH_IRI)
    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    dc = sg.value(subject=including_graph_iri, predicate=SDO.dateCreated)
    assert dc.value == datetime.datetime.strptime(
        "2026-01-01T17:25:32", "%Y-%m-%dT%H:%M:%S"
    )
    dm = sg.value(subject=including_graph_iri, predicate=SDO.dateModified)
    assert dm.value > start_time

    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/a")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/b")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/x")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/y")) in sg

    # reset test file
    with open(target_sg, "w") as f:
        f.write(dataset_trig)


def test_include_sparql(fuseki_container):
    sparql_endpoint = f"http://localhost:{fuseki_container.get_exposed_port(3030)}/ds"
    including_graph_iri = URIRef("http://example.org/g/1")

    kurra.db.gsp.put(sparql_endpoint, basic_vg, str(SYSTEM_GRAPH_IRI))
    kurra.db.gsp.put(sparql_endpoint, simple_rg_01, "http://example.org/g/1")
    kurra.db.gsp.put(sparql_endpoint, simple_rg_02, "default")

    include(
        including_graph_iri,
        ["http://example.org/g/x", "http://example.org/g/y"],
        sparql_endpoint,
    )

    sg = kurra.db.gsp.get(sparql_endpoint, SYSTEM_GRAPH_IRI)
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/a")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/b")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/x")) in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/y")) in sg


def test_exclude_local_dataset():
    start_time = datetime.datetime.now()
    time.sleep(1)
    target_sg = this_dir / "ogf" / "04-local-dataset.trig"
    including_graph_iri = URIRef("http://example.org/g/1")
    exclude(
        including_graph_iri,
        ["http://example.org/g/a", "http://example.org/g/z"],
        target_sg,
    )

    local_dataset = Dataset().parse(target_sg, format="trig")
    sg = local_dataset.get_graph(SYSTEM_GRAPH_IRI)
    assert (including_graph_iri, RDF.type, OLIS.VirtualGraph) in sg
    dc = sg.value(subject=including_graph_iri, predicate=SDO.dateCreated)
    assert dc.value == datetime.datetime.strptime(
        "2026-01-01T17:25:32", "%Y-%m-%dT%H:%M:%S"
    )
    dm = sg.value(subject=including_graph_iri, predicate=SDO.dateModified)
    assert dm.value > start_time

    assert (
        including_graph_iri,
        OLIS.includes,
        URIRef("http://example.org/g/a"),
    ) not in sg
    assert (including_graph_iri, OLIS.includes, URIRef("http://example.org/g/b")) in sg

    # reset test file
    with open(target_sg, "w") as f:
        f.write(dataset_trig)


def test_validate_system_graph():
    valid_sg = dedent(
        """
        PREFIX ex: <http://example.com/>
        PREFIX olis: <https://olis.dev/>
        
        ex:rg-1
            a olis:RealGraph ;
        .
        
        ex:rg-2
            a olis:VirtualGraph ;
        .
        """
    )

    invalid_sg = dedent(
        """
        PREFIX ex: <http://example.com/>
        PREFIX olis: <https://olis.dev/>
        
        ex:rg-1
            a
                olis:RealGraph ,
                olis:VirtualGraph ;
        .
        """
    )

    v = validate_system_graph(valid_sg)
    assert v[0]

    v = validate_system_graph(invalid_sg)
    assert not v[0]
