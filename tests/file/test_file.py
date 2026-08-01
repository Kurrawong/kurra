import warnings
from pathlib import Path
from textwrap import dedent

import pytest
from rdflib import Dataset, Graph, URIRef

import kurra.file
from kurra.file import (
    _format_file,
    export_quads,
    hierarchy,
    make_dataset,
    merge,
    reformat,
)
from kurra.utils import load_graph


def test_merge_prints_turtle(tmp_path, capsys):
    turtle_file = tmp_path / "first.ttl"
    turtle_file.write_text(
        "@prefix ex: <http://example.com/> . ex:a ex:p ex:b .",
        encoding="utf-8",
    )
    xml_file = tmp_path / "second.rdf"
    Graph().parse(
        data="@prefix ex: <http://example.com/> . ex:c ex:p ex:d .",
        format="turtle",
    ).serialize(destination=xml_file, format="xml")

    merge(turtle_file, xml_file)

    merged = Graph().parse(data=capsys.readouterr().out, format="turtle")
    assert len(merged) == 2


def test_merge_writes_requested_format(tmp_path):
    first = tmp_path / "first.nt"
    first.write_text(
        "<http://example.com/a> <http://example.com/p> <http://example.com/b> .\n",
        encoding="utf-8",
    )
    second = tmp_path / "second.ttl"
    second.write_text(
        "@prefix ex: <http://example.com/> . ex:c ex:p ex:d .",
        encoding="utf-8",
    )
    destination = tmp_path / "merged.jsonld"

    merge(first, second, destination=destination, output_format="json-ld")

    merged = Graph().parse(destination, format="json-ld")
    assert len(merged) == 2


def test_reformat_rdf_one():
    input_file = Path(__file__).parent / "minimal1.ttl"
    output_file = Path(__file__).parent / "minimal1-out.ttl"
    comparison = """PREFIX ex: <http://example.com/>

ex:a
    ex:b ex:c ;
."""

    _format_file(input_file, False, output_filename=output_file)
    output_file_text = output_file.read_text().strip().replace("ns1", "ex")

    assert output_file_text == comparison

    output_file.unlink(missing_ok=True)

    input_file = Path(__file__).parent / "minimal1b.ttl"
    output_file = Path(__file__).parent / "minimal1b-out.ttl"
    # same comparison data

    _format_file(input_file, False, output_filename=output_file)
    output_file_text = output_file.read_text().strip().replace("ns1", "ex")

    assert output_file_text == comparison

    output_file.unlink(missing_ok=True)


def test_reformat_headers():
    input_file = Path(__file__).parent / "header.ttl"
    output_file = input_file.with_suffix(".2.ttl")
    kurra.file.reformat(input_file, False, output_filename=output_file)

    expected = dedent(
        """
        # some pointless comment
        
        # another
        
        PREFIX ex: <http://example.com/>
        
        ex:a
            ex:b ex:c ;
        .
        """
    ).strip()

    with open(output_file) as f:
        actual = f.read().strip()

    assert expected == actual

    Path.unlink(output_file, missing_ok=True)


def test_make_dataset():
    g = load_graph(
        """
        PREFIX ex: <http://example.com/>
        
        ex:a ex:b ex:c . 
        """
    )

    d = make_dataset(g, "http://graph.com/a")

    for t in d.quads():
        assert t[0] == URIRef("http://example.com/a")
        assert t[1] == URIRef("http://example.com/b")
        assert t[2] == URIRef("http://example.com/c")
        assert t[3] == URIRef("http://graph.com/a")


@pytest.mark.parametrize(
    ("fixture_name", "expected_output"),
    [
        (
            "hierarchy-vocab.ttl",
            dedent(
                """\
                ex:voc
                ├── ex:1
                │   ├── ex:11
                │   ├── ex:12
                │   └── ex:13
                └── ex:2
                """
            ),
        ),
        (
            "hierarchy-ont.ttl",
            dedent(
                """\
                ex:Fruits
                ├── ex:Berry
                │   └── ex:Strawberry
                ├── ex:CitrusFruit
                │   ├── ex:Lemon
                │   ├── ex:Lime
                │   └── ex:Orange
                │       ├── ex:BloodOrange
                │       └── ex:SevilleOrange
                └── ex:StoneFruit
                    ├── ex:Cherry
                    ├── ex:Peach
                    └── ex:Plum
                """
            ),
        ),
    ],
)
def test_hierarchy_rendering_regression(fixture_name, expected_output, capsys):
    hierarchy(Path(__file__).parent / fixture_name)

    assert capsys.readouterr().out == expected_output


def test_hierarchy_prints_classes_properties_and_concepts(capsys):
    hierarchy(
        """
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .

        ex:Animal a owl:Class .
        ex:Cat a owl:Class ; rdfs:subClassOf ex:Animal .
        ex:Dog a rdfs:Class ; rdfs:subClassOf ex:Animal .

        ex:relatedTo a rdf:Property .
        ex:parentOf a owl:ObjectProperty ; rdfs:subPropertyOf ex:relatedTo .

        ex:scheme a skos:ConceptScheme .
        ex:thing a skos:Concept ; skos:inScheme ex:scheme ; skos:narrower ex:widget .
        ex:widget a skos:Concept ; skos:inScheme ex:scheme ; skos:broader ex:thing .
        """,
    )

    assert capsys.readouterr().out == dedent(
        """\
        ex:Animal
        ├── ex:Cat
        └── ex:Dog

        ex:relatedTo
        └── ex:parentOf

        ex:scheme
        └── ex:thing
            └── ex:widget
        """
    )


def test_hierarchy_uses_explicit_skos_top_concept_links(capsys):
    hierarchy(
        """
        @prefix ex: <http://example.com/> .
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .

        ex:scheme a skos:ConceptScheme ; skos:hasTopConcept ex:top .
        ex:top a skos:Concept ; skos:topConceptOf ex:scheme .
        ex:child a skos:Concept ; skos:broader ex:top .
        """
    )

    assert capsys.readouterr().out == (
        "ex:scheme\n└── ex:top\n    └── ex:child\n"
    )


def test_hierarchy_uses_ontology_as_class_and_property_root(capsys):
    hierarchy(
        """
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

        ex:ontology a owl:Ontology .
        ex:Animal a owl:Class .
        ex:Cat a owl:Class ; rdfs:subClassOf ex:Animal .
        ex:relatedTo a owl:ObjectProperty .
        ex:parentOf a owl:ObjectProperty ; rdfs:subPropertyOf ex:relatedTo .
        """
    )

    assert capsys.readouterr().out == dedent(
        """\
        ex:ontology
        └── ex:Animal
            └── ex:Cat

        ex:ontology
        └── ex:relatedTo
            └── ex:parentOf
        """
    )


def test_hierarchy_can_use_names_in_priority_order(capsys):
    hierarchy(
        """
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix schema: <https://schema.org/> .
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .

        ex:ontology a owl:Ontology ; dcterms:title "Fruit ontology" ;
            rdfs:label "Ignored ontology label" .
        ex:Fruit a owl:Class ; schema:name "Fruit name" ;
            rdfs:label "Ignored fruit label" .
        ex:Apple a owl:Class ; rdfs:subClassOf ex:Fruit ;
            skos:prefLabel "Apple preferred" ; dcterms:title "Ignored title" ;
            schema:name "Ignored name" ; rdfs:label "Ignored label" .
        ex:GrannySmith a owl:Class ; rdfs:subClassOf ex:Apple ;
            rdfs:label "Granny Smith" .
        ex:Unnamed a owl:Class ; rdfs:subClassOf ex:Fruit .
        """,
        use_names=True,
    )

    assert capsys.readouterr().out == dedent(
        """\
        Fruit ontology
        └── Fruit name
            ├── Apple preferred
            │   └── Granny Smith
            └── ex:Unnamed
        """
    )


def test_hierarchy_raises_on_cycles(capsys):
    graph = Graph().parse(
        data="""
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:A a owl:Class ; rdfs:subClassOf ex:B .
        ex:B a owl:Class ; rdfs:subClassOf ex:A .
        ex:C a owl:Class .
        ex:D a owl:Class ; rdfs:subClassOf ex:C .
        """,
        format="turtle",
    )

    with pytest.raises(
        ValueError,
        match=r"Cycle detected in hierarchy: ex:A -> ex:B -> ex:A",
    ):
        hierarchy(graph)

    assert capsys.readouterr().out == ""


def test_hierarchy_selects_named_graph(tmp_path, capsys):
    trig_file = tmp_path / "hierarchies.trig"
    trig_file.write_text(
        """
        @prefix ex: <http://example.com/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        ex:wanted {
            ex:Animal a owl:Class .
            ex:Cat a owl:Class ; rdfs:subClassOf ex:Animal .
        }
        ex:ignored {
            ex:Vehicle a owl:Class .
            ex:Car a owl:Class ; rdfs:subClassOf ex:Vehicle .
        }
        """,
        encoding="utf-8",
    )

    hierarchy(trig_file, "http://example.com/wanted")

    assert capsys.readouterr().out == "ex:Animal\n└── ex:Cat\n"


@pytest.mark.parametrize(
    "source",
    [Graph(), "@prefix owl: <http://www.w3.org/2002/07/owl#> ."],
)
def test_hierarchy_rejects_graph_iri_for_contextless_source(source):
    with pytest.raises(ValueError, match="graph_iri is only allowed"):
        hierarchy(source, "http://example.com/graph")


def test_export_quads():
    g = Graph()
    g.parse(
        data="""
            PREFIX ex: <http://example.com/>

            ex:a ex:b ex:c . 
            """,
        format="turtle",
    )

    d = make_dataset(g, "http://graph.com/a")

    qds = export_quads(d)

    warnings.filterwarnings(
        "ignore", category=DeprecationWarning
    )  # ignore RDFLib's ConjunctiveGraph warning
    d2 = Dataset()
    d2.parse(data=qds, format="trig")

    for t in d.quads():
        assert t[0] == URIRef("http://example.com/a")
        assert t[1] == URIRef("http://example.com/b")
        assert t[2] == URIRef("http://example.com/c")
        assert t[3] == URIRef("http://graph.com/a")


def test_sparql():
    # x = subprocess.check_output(
    #     ["kurra", "query", "--f", "table", "tests/minimal1.ttl", "ASK { ?s ?p ?o}"]
    # )
    #
    # print(x)
    pass


# TODO: NC: solution not found yet to carry the namespaces from the graph through to serialization
def test_prefixes():
    input_file = Path(__file__).parent / "prefixes-test.ttl"
    output_file = Path(__file__).parent / "prefixes-test-out.ttl"
    comparison = dedent(
        """
        PREFIX ex: <http://example.com/>
        PREFIX other: <http://other.com/>
        PREFIX sss: <https://schema.org/>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        
        ex:a
            ex:b other:c ;
        .
        
        ex:x 
            a skos:ConceptScheme ; 
            ex:b sss:y ;
        .
        """
    )

    _format_file(input_file, False, output_filename=output_file)

    # assert output_file == comparison

    output_file.unlink(missing_ok=True)


def test_prefixes_issue_28(tmp_path):
    input_file = Path(__file__).parent / "prefixes-test-issue-28.ttl"
    output_file = tmp_path / "output.ttl"

    expected_output = dedent(
        """PREFIX : <http://base/#>
PREFIX bibo: <http://purl.org/ontology/bibo/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX ex: <http://example.org/>
PREFIX fuseki: <http://jena.apache.org/fuseki#>
PREFIX geosparql: <http://jena.apache.org/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX tdb2: <http://jena.apache.org/2016/tdb#>
PREFIX text: <http://jena.apache.org/text#>

:fake
    a bibo:book ;
    ex:title "Fake Book" ;
    fuseki:fake ex:Fake ;
    geosparql:hasGeometry
        [
            geosparql:asWKT "POINT (1, 0)" ;
        ] ;
    text:label "Fake Text" ;
    dc:title "Fake Book" ;
    dcterms:title "Fake Book" ;
    rdfs:type ex:Book ;
    skos:topConceptOf tdb2:FakeScheme ;
    schema:name "Fake Book" ;
.
"""
    )

    reformat(input_file, check=False, output_format="longturtle", output_filename=output_file)

    actual_out = output_file.read_text(encoding="utf-8")

    assert actual_out == expected_output


def test_directory():
    d = Path(__file__).parent

    expected_files = d.glob("**/*.jsonld")

    reformat(d, False, output_format="json-ld")

    # keep the input JSON-LD file
    for ef in expected_files:
        if ef.name != "minimal5.jsonld":
            print(f"removing {ef}")
            ef.unlink()


def test_quads():
    d = Path(__file__).parent

    export_quads(
        make_dataset(d / "minimal2.ttl", "http://example.com/x/"), d / "minimal2.nt"
    )

    assert Path(d / "minimal2.nt").exists()
    assert "http://example.com/x/" in Path(d / "minimal2.nt").read_text()

    Path(d / "minimal2.nt").unlink()


def test_merge():
    d = Path(__file__).parent
    merge(
        d / "minimal1.ttl",
        d / "minimal2.ttl",
        destination=d / "merged.nt",
        output_format="nt",
    )

    assert Path(d / "merged.nt").exists()
    assert "http://example.com/b" in Path(d / "merged.nt").read_text()
    assert "http://example.com/b2" in Path(d / "merged.nt").read_text()

    Path(d / "merged.nt").unlink()
