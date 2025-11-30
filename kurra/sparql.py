import json
from pathlib import Path
from typing import Literal

import httpx
from rdflib import Graph, Dataset

from kurra.db import make_sparql_dataframe
from kurra.db import sparql
from kurra.utils import load_graph


def query(
    p: Path | str | Graph | Dataset,
    q: str,
    http_client: httpx.Client = None,
    return_format: Literal["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
):
    if return_format not in ["original", "python", "dataframe"]:
        raise ValueError("return_format must be either 'original', 'python' or 'dataframe'")

    if return_format == "dataframe":
        if "CONSTRUCT" in q or "DESCRIBE" in q or "INSERT" in q or "DELETE" in q or "DROP" in q:
            raise ValueError("Only SELECT and ASK queries can have return_format set to \"dataframe\"")

        try:
            from pandas import DataFrame
        except ImportError:
            raise ValueError("You selected the output format \"dataframe\" by the pandas Python package is not installed.")

    if "CONSTRUCT" in q or "DESCRIBE" in q:
        if isinstance(p, str) and p.startswith("http"):
            if http_client is None:
                http_client = httpx.Client()

            headers = {
                "Content-Type": "application/sparql-query",
                "Accept": "text/turtle"
            }
            r = http_client.post(p, content=q, headers=headers)

            return Graph().parse(data=r.text, format="turtle")

        if isinstance(p, str) and not p.startswith("http"):
            # parse it and handle it as a Graph
            p = load_graph(p)

        if isinstance(p, Path):
            p = load_graph(p)

        # if we are here, path_str_graph_or_sparql_endpoint is a Graph
        r = p.query(q)
        return r.graph
    elif "INSERT" in q or "DELETE" in q:
        raise NotImplementedError("INSERT & DELETE queries are not yet implemented by this interface. Try kurra.db.sparql")
    elif "DROP" in q:
        if isinstance(p, str) and p.startswith("http"):
            r = sparql(p, q, http_client, return_format, False)

            if r == "":
                return ""
        else:
            raise NotImplementedError("DROP commands are not yet implemented for files")
    else:  # SELECT or ASK
        close_http_client = False
        if http_client is None:
            http_client = httpx.Client()
            close_http_client = True

        r = None
        if isinstance(p, str) and p.startswith("http"):
            r = sparql(p, q, http_client, "python", False)

        if r is None:
            x = load_graph(p).query(q)
            r = json.loads(x.serialize(format="json"))

        if close_http_client:
            http_client.close()

        if return_bindings_only:
            if r.get("results") is not None:
                r = r["results"]["bindings"]
            elif r.get("boolean") is not None:  # ASK
                r = r["boolean"]
            else:
                pass

        if return_format == "python":
            return r
        elif return_format == "dataframe":
            return make_sparql_dataframe(r)
        else:  # original
            return json.dumps(r)
