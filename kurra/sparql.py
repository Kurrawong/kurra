from pathlib import Path

from rdflib import Graph

from kurra.db import sparql
from kurra.utils import load_graph


def query(path_str_graph_or_sparql_endpoint: Path | str | Graph, q: str):
    r = None
    if isinstance(path_str_graph_or_sparql_endpoint, str):
        if path_str_graph_or_sparql_endpoint.startswith("http"):
            r = sparql(path_str_graph_or_sparql_endpoint, q, None, True, False)

    if r is None:
        r = load_graph(path_str_graph_or_sparql_endpoint).query(q)

    return r
