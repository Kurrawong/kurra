"""SPARQL Graph Store Protocol functions.

These are known to work well with Jena Fuseki and GraphDB but may need testing for other RDF Database implementations due to differences in repository/dataset endpoints some of them use. See [`utils.make_system_specific_sparql_endpoint()`][kurra.utils.make_system_specific_sparql_endpoint] for some endpoint difference handling.
"""

from pathlib import Path
from typing import Literal as LiteralType
from typing import Union

import httpx
from rdflib import Graph

from kurra.db.sparql import query
from kurra.utils import (
    RDF_SUFFIX_MAP,
    GspType,
    load_graph,
    make_system_specific_sparql_endpoint,
)


def exists(
    sparql_endpoint: str, graph_iri: str, http_client: httpx.Client | None = None
) -> bool:
    """Check whether a graph exists at a SPARQL endpoint.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        graph_iri: The IRI of the graph to check. If None, the default graph is checked.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        True if the graph exists, False otherwise.

    Raises:
        ValueError: If `sparql_endpoint` does not start with "http".
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError("SPARQL Endpoint given does not start with 'http'")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    ssse = make_system_specific_sparql_endpoint(
        sparql_endpoint, gsp_query_type=GspType.get
    )

    if graph_iri is None:
        ssse += "?default"

    r = http_client.head(
        ssse,
        params={"graph": graph_iri} if graph_iri is not None else None,
    )

    if close_http_client:
        http_client.close()

    return r.is_success


def get(
    sparql_endpoint: str,
    graph_iri: str = None,
    accept_type: str = "text/turtle",
    return_format: LiteralType["original", "python"] = "python",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's [HTTP GET](https://www.w3.org/TR/sparql12-graph-store-protocol/#http-get).

    Returns the content of the graph identified by `graph_iri` in the target SPARQL Endpoint.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        graph_iri: The IRI of the graph to retrieve.
        accept_type: The RDF format to request from the server and to return if return_format is set to "original".
        return_format: `"python"` for RDFLib's Graph, `"original"` for an RDF string value in the format of `accept_type`.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
          An RDF result as either an RDFLib Graph object or a string object containing RDF in the accept_type
          format. If a graph, the graph identifier will be the graph_iri or a Blank Node if None/default

    Raises:
        ValueError: If `sparql_endpoint` does not start with "http", `accept_type` is not a supported RDF media type, or `return_format` is invalid.
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError("SPARQL Endpoint given does not start with 'http'")

    if accept_type not in RDF_SUFFIX_MAP.values():
        raise ValueError(
            f"Media Type requested not available. Allow types are {', '.join(RDF_SUFFIX_MAP.values())}"
        )

    if return_format not in ["original", "python"]:
        raise ValueError(
            "Return format must be either 'python' (default) or 'original'"
        )

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    ssse = make_system_specific_sparql_endpoint(
        sparql_endpoint, gsp_query_type=GspType.get
    )

    if graph_iri is None:
        ssse += "?default"

    r = http_client.get(
        ssse,
        params={"graph": graph_iri} if graph_iri is not None else None,
        headers={"Accept": accept_type},
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        if return_format == "original":
            return r.text
        else:
            if graph_iri is not None and graph_iri != "default":
                return Graph(identifier=graph_iri).parse(
                    data=r.text, format=accept_type
                )
            else:
                return Graph().parse(data=r.text, format=accept_type)
    else:
        return r.status_code, r.text


def put(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_iri: str = None,
    content_type: str = "text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's [HTTP PUT](https://www.w3.org/TR/sparql12-graph-store-protocol/#http-put).

    Inserts the RDF content supplied into a graph identified by `graph_iri` or the default graph, replacing existing content.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        file_or_str_or_graph: The RDF content to insert as a file path, an RDF string, or a Graph.
        graph_iri: The IRI of the graph to insert into. If None, the default graph is targeted.
        content_type: The RDF media type to serialize the content as.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A tuple of `(True, None)` on success, or `(status_code, response_text)` on failure.

    Raises:
        ValueError: If `sparql_endpoint` does not start with "http", or `content_type` is not a supported RDF media type.
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError("SPARQL Endpoint given does not start with 'http'")

    if content_type not in RDF_SUFFIX_MAP.values():
        raise ValueError(
            f"Media Type {content_type} requested not available. Allowed types are {', '.join(RDF_SUFFIX_MAP.values())}"
        )

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    ssse = make_system_specific_sparql_endpoint(
        sparql_endpoint, gsp_query_type=GspType.put
    )

    if graph_iri is None:
        ssse += "?default"

    r = http_client.put(
        ssse,
        params={"graph": graph_iri} if graph_iri is not None else None,
        headers={"Content-Type": content_type},
        content=load_graph(file_or_str_or_graph).serialize(format=content_type),
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True, None
    else:
        return r.status_code, r.text


def post(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_iri: str = None,
    content_type: str = "text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's [HTTP POST](https://www.w3.org/TR/sparql12-graph-store-protocol/#http-post).

    Inserts the RDF content supplied into a graph identified by `graph_iri` or the default graph, adding to existing content.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        file_or_str_or_graph: The RDF content to insert as a file path, an RDF string, or a Graph.
        graph_iri: The IRI of the graph to insert into. If None, the default graph is targeted.
        content_type: The RDF media type to serialize the content as.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A tuple of `(True, None)` on success, or `(status_code, response_text)` on failure.

    Raises:
        ValueError: If `sparql_endpoint` does not start with "http", or `content_type` is not a supported RDF media type.
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError("SPARQL Endpoint given does not start with 'http'")

    if content_type not in RDF_SUFFIX_MAP.values():
        raise ValueError(
            f"Media Type requested not available. Allow types are {', '.join(RDF_SUFFIX_MAP.values())}"
        )

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    ssse = make_system_specific_sparql_endpoint(
        sparql_endpoint, gsp_query_type=GspType.post
    )

    if graph_iri is None:
        ssse += "?default"

    r = http_client.post(
        ssse,
        params={"graph": graph_iri} if graph_iri is not None else None,
        headers={
            "Content-Type": content_type,
        },
        content=load_graph(file_or_str_or_graph).serialize(format=content_type),
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True, None
    else:
        return r.status_code, r.text


def delete(
    sparql_endpoint: str,
    graph_iri: str = None,
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's [HTTP DELETE](https://www.w3.org/TR/sparql12-graph-store-protocol/#http-delete).

    Deletes the graph identified by `graph_iri`, or the default graph if not given.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        graph_iri: The IRI of the graph to delete. If None, the default graph is targeted.
        http_client: An HTTP client to use. Created internally if not supplied.

    Returns:
        A tuple of `(True, None)` on success, or `(status_code, response_text)` on failure.

    Raises:
        ValueError: If `sparql_endpoint` does not start with "http".
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError("SPARQL Endpoint given does not start with 'http'")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    ssse = make_system_specific_sparql_endpoint(
        sparql_endpoint, gsp_query_type=GspType.delete
    )

    if graph_iri is None:
        ssse += "?default"

    r = http_client.delete(
        ssse,
        params={"graph": graph_iri} if graph_iri is not None else None,
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True, None
    else:
        return r.status_code, r.text


def clear(
    sparql_endpoint: str, graph_iri: str, http_client: httpx.Client | None = None
) -> Union[Graph, int]:
    """Clear/Remove all triples from a graph identified by `graph_iri`.

    Special values for graph_iri are "default" (clears the default graph) and "all" (clears every graph). Operates much like SPARQL Update's [Clear function](https://www.w3.org/TR/sparql12-update/#clear), but uses GSP DELETE under the hood.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        graph_iri: The IRI of the graph to clear, or "default"/"all".
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A tuple of `(True, None)` if at least one graph was cleared successfully (for "all"), or the result of the underlying `delete` call otherwise.
    """
    if graph_iri == "default":
        return delete(sparql_endpoint, None, http_client=http_client)
    elif graph_iri == "all":
        # list all graphs in system
        deletion_results = []
        q = """
            SELECT DISTINCT ?g
            WHERE {
                GRAPH ?g {
                    ?s ?p ?o
                }
            }
            ORDER BY ?g
            """
        for r in query(
            sparql_endpoint,
            q,
            http_client=http_client,
            return_format="python",
            return_bindings_only=True,
        ):
            deletion_results.append(
                delete(sparql_endpoint, r["g"], http_client=http_client)
            )
        deletion_results.append(
            delete(sparql_endpoint, None, http_client=http_client)
        )  # default graph too

        # if even one graph is deleted correctly, return true
        for dr in deletion_results:
            if dr[0]:
                return (True, None)
        return (False, None)
    else:
        return delete(sparql_endpoint, graph_iri, http_client)


def upload(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_id: str | None = None,
    append: bool = False,
    content_type: str = "text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[bool, int]:
    """Upload a file, string, or Graph to a SPARQL endpoint using the Graph Store Protocol.

    Uploads into the graph identified by graph_id (an IRI), or the default graph if not given. By default, replaces all content in the target graph; if `append` is True, adds to existing content instead. This is an alias for `put` (`append=False`) and `post` (`append=True`).

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use.
        file_or_str_or_graph: The RDF content to upload as a file path, an RDF string, or a Graph.
        graph_id: The IRI of the graph to upload into. If None, the default graph is targeted.
        append: If True, add to existing content (via `post`) instead of replacing it (via `put`).
        content_type: The RDF media type to serialize the content as.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A tuple of `(True, None)` on success, or `(status_code, response_text)` on failure.
    """

    if append:
        return post(
            sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client
        )
    else:
        return put(
            sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client
        )
