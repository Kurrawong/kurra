# Graph Store Protocol

from pathlib import Path
from typing import Literal as LiteralType
from typing import Union

import httpx
from rdflib import Graph

from kurra.utils import RDF_SUFFIX_MAP, load_graph


def exists(
    sparql_endpoint: str, graph_iri: str, http_client: httpx.Client | None = None
) -> bool:
    """Returns True if a graph with the given graph_iri exists at the SPARQL Endpoint or else False"""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if not graph_iri:
        raise ValueError("You must supply a graph IRI")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.head(
        sparql_endpoint,
        params={"graph": graph_iri if graph_iri is not None else "default"},
    )

    if close_http_client:
        http_client.close()

    return r.is_success


def get(
    sparql_endpoint: str,
    graph_iri: str = "default",
    accept_type="text/turtle",
    return_format: LiteralType["original", "python"] = "python",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP GET: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-get

    Returns the content of the graph identified by graph_id in the target SPARQL Endpoint.

    Args:
        sparql_endpoint: The SPARQL Endpoint URL to use
        graph_iri: The IRI of the graph to retrieve
        accept_type: The RDF format to request from the server and to return if return_format is set to 'original'
        return_format: The return format to use, 'python' - RDFLib's Graph - or 'original' - an RDF string value in the format of accept_type
        http_client: An HTTP client to use. Created internally if not supplied

    Returns:
          An RDF result as either an RDFLib Graph object or a string object containing RDF in the accept_type
          format. If a graph, the graph identifier will be the graph_iri or a Blank Node if None/default
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

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

    r = http_client.get(
        sparql_endpoint,
        params={"graph": graph_iri if graph_iri is not None else "default"},
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
        return r.status_code


def put(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_iri: str = "default",
    content_type="text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP PUT: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-put

    Inserts the RDF content supplied into a graph identified by graph_id or the default graph.

    Will replace existing content."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if content_type not in RDF_SUFFIX_MAP.values():
        raise ValueError(
            f"Media Type {content_type} requested not available. Allowed types are {', '.join(RDF_SUFFIX_MAP.values())}"
        )

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True
    r = http_client.put(
        sparql_endpoint,
        params={"graph": graph_iri if graph_iri is not None else "default"},
        headers={"Content-Type": content_type},
        content=load_graph(file_or_str_or_graph).serialize(format=content_type),
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True
    else:
        return r.status_code


def post(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_iri: str = "default",
    content_type="text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP POST: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-post

    Inserts the RDF content supplied into a graph identified by graph_id or the default graph.

    Will add to existing content."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if content_type not in RDF_SUFFIX_MAP.values():
        raise ValueError(
            f"Media Type requested not available. Allow types are {', '.join(RDF_SUFFIX_MAP.values())}"
        )

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.post(
        sparql_endpoint,
        params={"graph": graph_iri if graph_iri is not None else "default"},
        headers={
            "Content-Type": content_type,
        },
        content=load_graph(file_or_str_or_graph).serialize(format=content_type),
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True
    else:
        return r.status_code


def delete(
    sparql_endpoint: str,
    graph_iri: str = "default",
    http_client: httpx.Client | None = None,
) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP DELETE: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-delete

    Deletes the graph identified by graph_id or the default graph."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.delete(
        sparql_endpoint,
        params={"graph": graph_iri if graph_iri is not None else "default"},
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True
    else:
        return r.status_code


def clear(
    sparql_endpoint: str, graph_iri: str, http_client: httpx.Client | None = None
):
    """SPARQL Update Clear function: https://www.w3.org/TR/sparql12-update/#clear

    Clears - remove all triples from - an identified graph or from all graphs if "all" is given as the graph_id.

    This is an alias of delete()
    """
    delete(sparql_endpoint, graph_iri, http_client)


def upload(
    sparql_endpoint: str,
    file_or_str_or_graph: Union[Path, str, Graph],
    graph_id: str | None = None,
    append: bool = False,
    content_type: str = "text/turtle",
    http_client: httpx.Client | None = None,
) -> Union[bool, int]:
    """This function uploads a file to a SPARQL Endpoint using the Graph Store Protocol.

    It will upload it into a graph identified by graph_id (an IRI or Blank Node). If no graph_id is given, it will be
    uploaded into the default graph.

    By default, it will replace all content in the Named Graph or default graph. If append is set to True, it will
    add it to existing content in the graph_id Named Graph.

    This function is an alias of put() (append=False) and post() (append=True)."""

    if append:
        return post(
            sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client
        )
    else:
        return put(
            sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client
        )
