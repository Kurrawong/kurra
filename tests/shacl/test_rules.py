from pathlib import Path

from rdflib.compare import isomorphic

from kurra.shacl import infer
from kurra.utils import load_graph


def test_rules():
    data_graph = Path(__file__).parent / "infer" / "01-data.ttl"

    rules = Path(__file__).parent / "infer" / "01-rules.srl"

    results_graph_expected = load_graph(
        Path(__file__).parent / "infer" / "01-results.ttl"
    )

    results_graph_received = infer(data_graph, rules)

    assert isomorphic(results_graph_expected, results_graph_received)
