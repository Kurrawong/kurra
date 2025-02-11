from pathlib import Path

from pyshacl import validate as v
from rdflib import Graph

from kurra.utils import load_graph


def validate(
    data_file_or_dir_or_graph: Path | Graph, shacl_file_or_dir_or_graph: Path | Graph
) -> tuple[bool, Graph, str]:
    """Runs pySHACL's validate() function with some preset values"""

    data_graph = load_graph(data_file_or_dir_or_graph)
    shapes_graph = load_graph(shacl_file_or_dir_or_graph)

    return v(data_graph, shacl_graph=shapes_graph, allow_warnings=True)
