from pathlib import Path

import pytest
from rdflib import Graph

from kurra.labels import SPLIT_REGEX, find_missing_labels, get_labels, jsonld_context


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

    assert type(rdf) == Graph
    assert len(rdf) == 32

    rdf = get_labels(
        find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl"),
        return_type="dict",
    )

    assert type(rdf) == dict
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
