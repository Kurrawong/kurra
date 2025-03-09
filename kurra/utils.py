import httpx
import json
from enum import Enum
from pathlib import Path
from typing import Union
import pickle
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


def load_graph(graph_path_or_str: Union[Graph, Path, str], recursive=False) -> Graph:
    """
    Presents an RDFLib Graph object from a pre-existing Graph, a pickle file, an RDF file or directory of files or RDF
    data in a string
    """
    # Pre-existing Graph
    if isinstance(graph_path_or_str, Graph):
        return graph_path_or_str

    # Pickle file
    if isinstance(graph_path_or_str, Path):
        if graph_path_or_str.is_file():
            pkl_path = graph_path_or_str.with_suffix(".pkl")
            if pkl_path.is_file():
                return pickle.load(open(pkl_path, "rb"))

    # Serialized RDF file or dir of files
    if isinstance(graph_path_or_str, Path):
        if Path(graph_path_or_str).is_file():
            return Graph().parse(str(graph_path_or_str))
        elif Path(graph_path_or_str).is_dir():
            g = Graph()
            if recursive:
                gl = Path(graph_path_or_str).rglob("*.ttl")
            else:
                gl = Path(graph_path_or_str).glob("*.ttl")
            for f in gl:
                if f.is_file():
                    g.parse(f)
            return g

    # A remote file via HTTP
    elif isinstance(graph_path_or_str, str) and graph_path_or_str.startswith("http"):
        return Graph().parse(graph_path_or_str)

    # RDF data in a string
    else:
        return Graph().parse(
            data=graph_path_or_str,
            format=guess_format_from_data(graph_path_or_str),
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


def make_httpx_client(
    sparql_username: str = None,
    sparql_password: str = None,
):
    auth = None
    if sparql_username:
        if sparql_password:
            auth = httpx.BasicAuth(sparql_username, sparql_password)
    return httpx.Client(auth=auth)
