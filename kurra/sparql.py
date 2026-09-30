"""SPARQL query functions."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

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

if TYPE_CHECKING:
    from pandas import DataFrame


@overload
def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    *,
    namespaces: dict[str, str] | None,
    http_client: httpx.Client | None,
    return_format: Literal["original"] = "original",
    return_bindings_only: bool = False,
) -> str: ...
@overload
def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    *,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client | None = None,
    return_format: Literal["python"],
    return_bindings_only: bool = False,
) -> Graph: ...


@overload
def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    *,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client | None = None,
    return_format: Literal["dataframe"],
    return_bindings_only: bool = False,
) -> "DataFrame": ...
def query(
    p: Path | str | Graph | Dataset,
    q: str | Path,
    namespaces: dict[str, str] | None = None,
    http_client: httpx.Client | None = None,
    return_format: Literal["original", "python", "dataframe"] = "original",
    return_bindings_only: bool = False,
) -> "str | Graph | dict | DataFrame":
    """Run a SPARQL query or update against a file, RDF Graph/Dataset, or SPARQL endpoint.

    Args:
        p: A local file path, SPARQL endpoint URL, RDF string, Graph, or Dataset.
        q: The SPARQL query or update, as a string or a path to a file containing one.
        namespaces: Namespace prefixes to add to `q` before running it.
        http_client: An optional HTTPX client to contain credentials if needed to access a SPARQL endpoint when `p` is a URL. A new one is created if not given.
        return_format: `"original"` for the endpoint's raw response, `"python"` for parsed Python objects, or `"dataframe"` for a pandas DataFrame (SELECT/ASK only).
        return_bindings_only: If True, return just the result bindings rather than the full SPARQL results structure.

    Returns:
        The query result, in the requested `return_format`. CONSTRUCT/DESCRIBE queries always return a Graph (or its serialization), updates against a Graph, file, or RDF string return the updated Graph.

    Raises:
        ValueError: If `p` or `q` is not given, `return_format` is invalid, `return_format` is `"dataframe"` for a non-SELECT/ASK query, or pandas is not installed for `"dataframe"`.
        NotImplementedError: If a DROP update targets anything other than a Dataset, or an update targets a Dataset directly.
    """
    if p is None:
        raise ValueError(
            "You must supply a Path, string (of data or a URL), Graph or a Dataset to query for variable p"
        )

    if q is None:
        raise ValueError("You must supply a query")

    if isinstance(q, str):
        if len(q) < 260:
            if Path(q).is_file():
                q = Path(q).read_text()

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
            r = db_query(str(p), str(q), namespaces, http_client, "original", False)
            s = load_graph(r)

        else:  # (isinstance(p, str) and not p.startswith("http")) or isinstance(p, Path):
            f = load_graph(p).query(str(q))

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

            r = db_query(str(p), q, namespaces, http_client, return_format, False)

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
                str(p), q, namespaces, http_client, return_format, return_bindings_only
            )

            if close_http_client:
                http_client.close()

        if r is not None:  # we have a result from the DB query to return
            return r
        else:  # querying a file or string RDF data
            r = load_graph(p).query(str(q)).serialize(format="json")

            if return_format == "dataframe":
                return make_sparql_dataframe(json.loads(r))
            elif return_format == "python":
                return convert_sparql_json_to_python(r, return_bindings_only)
            else:
                return r.decode()
