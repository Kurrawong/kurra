import json
from pathlib import Path
from typing import Literal

import httpx
from rdflib import Dataset, Graph

from kurra.db.sparql import query as db_query
from kurra.utils import (
    add_namespaces_to_query_or_data,
    convert_sparql_json_to_python,
    is_construct_or_describe_query,
    is_drop_update,
    is_select_or_ask_query,
    is_update_query,
    load_graph,
    make_sparql_dataframe,
    statement_type_for_query,
)


def query(
    p: Path | str | Graph | Dataset,
    q: str,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client = None,
    return_format: Literal["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
):
    """Pose a SPARQL query to a file, and RDF Graph or a SPARQL Endpoint"""
    if p is None:
        raise ValueError(
            "You must supply a Path, string (of data or a URL), Graph or a Dataset to query for variable p"
        )

    if q is None:
        raise ValueError("You must supply a query")

    if return_format not in ["original", "python", "dataframe"]:
        raise ValueError(
            f"return_format {return_format} must be either 'original', 'python' or 'dataframe'"
        )

    if namespaces is not None:
        q = add_namespaces_to_query_or_data(q, namespaces)

    if http_client is None:
        http_client = httpx.Client()

    statement = statement_type_for_query(q)

    if return_format == "dataframe":
        if not is_select_or_ask_query(q, statement):
            raise ValueError(
                'Only SELECT and ASK queries can have return_format set to "dataframe"'
            )

        try:
            from pandas import DataFrame
        except ImportError:
            raise ValueError(
                'You selected the output format "dataframe" but the pandas Python package is not installed.'
            )

    if is_construct_or_describe_query(q, statement):
        s = None
        f = None
        if str(p).startswith("http"):
            r = db_query(p, q, namespaces, http_client, "original", False)
            s = load_graph(r)

        else:  # (isinstance(p, str) and not p.startswith("http")) or isinstance(p, Path):
            f = load_graph(p).query(q)

        if return_format == "dataframe":
            raise ValueError(
                "DataFrames cannot be returned for CONSTRUCT or DESCRIBE queries"
            )
        elif return_format == "python":
            return s if s is not None else f.graph
        else:
            return (
                s.serialize(format="longturtle")
                if s is not None
                else f.graph.serialize(format="longturtle")
            )

    elif is_update_query(q, statement):
        if str(p).startswith("http"):
            close_http_client = False
            if http_client is None:
                http_client = httpx.Client()
                close_http_client = True

            r = db_query(p, q, namespaces, http_client, return_format, False)

            if close_http_client:
                http_client.close()

            if r == "" or r is None:
                return ""

        if is_drop_update(q, statement) and not isinstance(p, Dataset):
            raise NotImplementedError(
                f"DROP commands cannot be applied to Graphs or files or triples data, only Datasets or RDF DBs. You specified {p}"
            )
        elif isinstance(p, (Graph, str, Path)):
            g = load_graph(p)
            g.update(q)
            return g
        else:
            raise NotImplementedError(
                "Update SPARQL commands on Datasets are not yet supported"
            )

    else:  # SELECT or ASK
        r = None
        if str(p).startswith("http"):
            close_http_client = False
            if http_client is None:
                http_client = httpx.Client()
                close_http_client = True

            r = db_query(
                p, q, namespaces, http_client, return_format, return_bindings_only
            )

            if close_http_client:
                http_client.close()

        if r is not None:  # we have a result from the DB query to return
            return r
        else:  # querying a file or string RDF data
            r = load_graph(p).query(q).serialize(format="json")

            if return_format == "dataframe":
                return make_sparql_dataframe(json.loads(r))
            elif return_format == "python":
                return convert_sparql_json_to_python(r, return_bindings_only)
            else:
                return r.decode()
