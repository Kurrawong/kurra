from pathlib import Path

import pytest
from rdflib import DCTERMS, RDFS, SDO, SKOS, XSD, BNode, Graph, Literal, Namespace

from kurra.labels import (
    SPLIT_REGEX,
    find_duplicate_labels,
    find_missing_labels,
    get_labels,
    jsonld_context,
)

EX = Namespace("http://example.com/")


@pytest.mark.parametrize(
    "second",
    [
        Literal("different"),
        Literal("label", lang="en"),
        Literal("label", datatype=XSD.string),
        Literal("label", datatype=EX.datatype),
    ],
)
def test_find_duplicate_labels_distinct_literals(second):
    graph = Graph()
    graph.add((EX.node, SDO.name, Literal("label")))
    graph.add((EX.node, RDFS.label, second))

    assert find_duplicate_labels(graph) == {EX.node: {Literal("label"), second}}


def test_find_duplicate_labels_distinct_languages():
    graph = Graph()
    graph.add((EX.node, SKOS.prefLabel, Literal("label", lang="en")))
    graph.add((EX.node, SKOS.prefLabel, Literal("label", lang="fr")))

    assert find_duplicate_labels(graph) == {
        EX.node: {Literal("label", lang="en"), Literal("label", lang="fr")}
    }


@pytest.mark.parametrize(
    "mode, predicates",
    [
        ("names", [SDO.name, RDFS.label, DCTERMS.title, SKOS.prefLabel]),
        (
            "descriptions",
            [SDO.description, RDFS.comment, DCTERMS.description, SKOS.definition],
        ),
    ],
)
def test_find_duplicate_labels_predicates(mode, predicates):
    graph = Graph()
    values = {Literal(str(index)) for index in range(len(predicates))}
    for index, predicate in enumerate(predicates):
        graph.add((EX.node, predicate, Literal(str(index))))

    assert find_duplicate_labels(graph, mode) == {EX.node: values}
    other_mode = "descriptions" if mode == "names" else "names"
    assert find_duplicate_labels(graph, other_mode) == {}


@pytest.mark.parametrize("mode", ["names", "descriptions"])
def test_find_duplicate_labels_additional_predicates(mode):
    graph = Graph()
    graph.add((EX.node, EX.annotation, Literal("first")))
    graph.add((EX.node, EX.annotation, Literal("second")))
    extra = [EX.annotation]

    assert find_duplicate_labels(graph, mode) == {}
    assert find_duplicate_labels(graph, mode, extra) == {
        EX.node: {Literal("first"), Literal("second")}
    }
    assert extra == [EX.annotation]
    assert find_duplicate_labels(graph, mode) == {}


def test_find_duplicate_labels_all_node_positions():
    graph = Graph()
    nodes = [EX.subject, EX.predicate, EX.object, BNode()]
    graph.add((EX.subject, EX.predicate, EX.object))
    for node in nodes:
        graph.add((node, RDFS.label, Literal("first")))
        graph.add((node, RDFS.label, Literal("second")))

    assert find_duplicate_labels(graph) == {
        node: {Literal("first"), Literal("second")} for node in nodes
    }


def test_find_duplicate_labels_ignores_repeated_values_and_non_literals():
    graph = Graph()
    graph.add((EX.node, RDFS.label, Literal("same")))
    graph.add((EX.node, SDO.name, Literal("same")))
    graph.add((EX.node, SKOS.prefLabel, EX.other))

    assert find_duplicate_labels(graph) == {}
    assert find_duplicate_labels(Graph()) == {}


@pytest.mark.parametrize("source_type", ["path", "string"])
def test_find_duplicate_labels_sources(tmp_path, source_type):
    rdf = (
        '<http://example.com/node> <http://www.w3.org/2000/01/rdf-schema#label> "first" .\n'
        '<http://example.com/node> <http://www.w3.org/2000/01/rdf-schema#label> "second" .\n'
    )
    if source_type == "path":
        source = tmp_path / "labels.nt"
        source.write_text(rdf)
    else:
        source = rdf

    assert find_duplicate_labels(source) == {
        EX.node: {Literal("first"), Literal("second")}
    }


def test_find_duplicate_labels_invalid_mode():
    with pytest.raises(ValueError, match="names_or_descriptions"):
        find_duplicate_labels(Graph(), "invalid")


@pytest.mark.parametrize(
    "text, expected",
    [
        ("has lithology", ["has", "lithology"]),
        ("has-lithology_type", ["has", "lithology", "type"]),
        ("geological unit/type", ["geological", "unit", "type"]),
        ("hasLithology", ["has", "Lithology"]),
        ("GeologicalUnit", ["Geological", "Unit"]),
        ("has_LithologyType example", ["has", "Lithology", "Type", "example"]),
    ],
)
def test_split_regex(text: str, expected: list[str]):
    assert SPLIT_REGEX.split(text) == expected


def test_find_missing_labels():
    lbls = find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl")

    assert len(lbls) == 42

    lbls = find_missing_labels(
        Path(__file__).parent / "GeologicMaterialTypes.ttl",
        Path(__file__).parent / "labels.ttl",
    )

    assert len(lbls) == 19


def test_get_missing_labels():
    rdf = get_labels(
        find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl")
    )

    assert type(rdf) is Graph
    assert len(rdf) == 32

    rdf = get_labels(
        find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl"),
        return_type="dict",
    )

    assert type(rdf) is dict
    assert len(rdf.keys()) == 32


def test_jsonld_context_pascal_and_camel_case():
    graph = Graph()
    graph.parse(
        data="""
        PREFIX ex: <http://example.com/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        ex:Sample1 a ex:GeologicalUnit ;
            ex:hasLithology ex:Basalt .

        ex:GeologicalUnit a owl:Class .
        """,
        format="turtle",
    )

    vocabulary = Graph()
    vocabulary.parse(
        data="""
        PREFIX ex: <http://example.com/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        ex:GeologicalUnit rdfs:label "geological unit" .
        ex:hasLithology rdfs:label "has lithology" .
        """,
        format="turtle",
    )

    context = jsonld_context(graph, vocabulary)

    # class labels are PascalCase
    assert context["GeologicalUnit"] == "http://example.com/GeologicalUnit"
    # property labels are camelCase
    assert context["hasLithology"] == "http://example.com/hasLithology"
