from pathlib import Path
from typing import Union
from rdflib import Graph


def guess_format_from_data(rdf: str):
    if rdf is not None:
        rdf = rdf.strip()
        if rdf.startswith("PREFIX") or rdf.startswith("@prefix"):
            return "text/turtle"
        elif rdf.startswith("{") or rdf.startswith("["):
            return "application/ld+json"
        elif rdf.startswith("<?xml") or rdf.startswith("<rdf"):
            return "application/rdf+xml"
        else:
            return "application/n-triples"
    else:
        return None


def load_graph(file_or_str_or_graph: Union[Path, str, Graph]):
    if isinstance(file_or_str_or_graph, Path):
        return Graph().parse(str(file_or_str_or_graph))

    elif isinstance(file_or_str_or_graph, Graph):
        return file_or_str_or_graph

    else:  # str (data)
        return Graph().parse(
            data=file_or_str_or_graph,
            format=guess_format_from_data(file_or_str_or_graph),
        )
