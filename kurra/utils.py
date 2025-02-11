from pathlib import Path
from typing import Union

from rdflib import Graph


def guess_format_from_data(rdf: str) -> str | None:
    if rdf is not None:
        rdf = rdf.strip()
        if rdf.startswith("PREFIX") or rdf.startswith("@prefix"):
            return "text/turtle"
        elif rdf.startswith("{") or rdf.startswith("["):
            return "application/ld+json"
        elif rdf.startswith("<?xml") or rdf.startswith("<rdf"):
            return "application/rdf+xml"
        elif rdf.startswith("<http"):
            return "application/n-triples"
        else:
            return "application/n-triples"
    else:
        return None


def load_graph(file_or_str_or_graph: Union[Path, str, Graph], recursive=False) -> Graph:
    """Presents an RDFLib Graph object from a parses source or a wrapper SPARQL Endpoint"""
    if isinstance(file_or_str_or_graph, Path):
        if Path(file_or_str_or_graph).is_file():
            return Graph().parse(str(file_or_str_or_graph))
        elif Path(file_or_str_or_graph).is_dir():
            g = Graph()
            if recursive:
                gl = Path(file_or_str_or_graph).rglob("*.ttl")
            else:
                gl = Path(file_or_str_or_graph).glob("*.ttl")
            for f in gl:
                if f.is_file():
                    g.parse(f)
            return g

    elif isinstance(file_or_str_or_graph, Graph):
        return file_or_str_or_graph

    else:  # str - data or SPARQL Endpoint
        return Graph().parse(
            data=file_or_str_or_graph,
            format=guess_format_from_data(file_or_str_or_graph),
        )
