import json
from enum import Enum
from pathlib import Path
from typing import Union

from rdflib import Graph


class RenderFormat(str, Enum):
    original = "original"
    json = "json"
    markdown = "markdown"


class SPARQL_RESULTS_MEDIA_TYPES(str, Enum):
    json = "application/json"
    turtle = "text/turtle"
    jsonld = "application/ld+json"


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

    elif file_or_str_or_graph.startswith("http"):
        return Graph().parse(file_or_str_or_graph)

    else:  # str - data or SPARQL Endpoint
        return Graph().parse(
            data=file_or_str_or_graph,
            format=guess_format_from_data(file_or_str_or_graph),
        )


def render_sparql_result(
    r: dict | str | Graph, rf: RenderFormat = RenderFormat.markdown
) -> str:
    """Renders a SPARQL result in a given render format"""
    if rf == RenderFormat.original:
        return r

    elif rf == RenderFormat.json:
        if isinstance(r, dict):
            return json.dumps(r, indent=4)
        elif isinstance(r, str):
            return json.dumps(json.loads(r), indent=4)
        elif isinstance(r, Graph):
            return r.serialize(format="json-ld", indent=4)

    elif rf == RenderFormat.markdown:
        if isinstance(r, Graph):  # CONSTRUCT: RDF GRaph
            output = "```turtle\n" + r.serialize(format="longturtle") + "```\n"
        else:  # SELECT or ASK: Python dict or JSON

            def render_sparql_value(v: dict) -> str:
                # TODO: handle v["datatype"]
                if v is None:
                    return ""
                elif v["type"] == "uri":
                    return f"[{v['value'].split('/')[-1].split('#')[-1]}]({v['value']})"
                elif v["type"] == "literal":
                    return v["value"]
                elif v["type"] == "bnode":
                    return f"BN: {v['value']:>6}"

            if isinstance(r, str):
                r = json.loads(r)

            output = ""
            header = ["", ""]
            body = []

            if r.get("head") is not None:
                # SELECT
                if r["head"].get("vars") is not None:
                    for col in r["head"]["vars"]:
                        header[0] += f"{col} | "
                        header[1] += f"--- | "
                    output = (
                        "| " + header[0].strip() + "\n| " + header[1].strip() + "\n"
                    )

            if r.get("results"):
                if r["results"].get("bindings"):
                    for row in r["results"]["bindings"]:
                        row_cols = []
                        for k in r["head"]["vars"]:
                            v = row.get(k)
                            if v is not None:
                                # ignore the k
                                row_cols.append(render_sparql_value(v))
                            else:
                                row_cols.append("")
                        body.append(" | ".join(row_cols))

                output += "\n| ".join(body) + " |\n"

            if r.get("boolean") is not None:
                output = str(bool(r.get("boolean")))

        return output
