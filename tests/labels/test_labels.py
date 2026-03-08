from pathlib import Path

from rdflib import Graph

from kurra.labels import find_missing_labels, get_missing_labels


def test_find_missing_labels():
    lbls = find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl")

    assert len(lbls) == 42

    lbls = find_missing_labels(
        Path(__file__).parent / "GeologicMaterialTypes.ttl",
        Path(__file__).parent / "labels.ttl",
    )

    assert len(lbls) == 19


def test_get_missing_labels():
    rdf = get_missing_labels(
        find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl")
    )

    assert type(rdf) == Graph
    assert len(rdf) == 29

    rdf = get_missing_labels(
        find_missing_labels(Path(__file__).parent / "GeologicMaterialTypes.ttl"),
        return_type="dict",
    )

    assert type(rdf) == dict
    assert len(rdf.keys()) == 29
