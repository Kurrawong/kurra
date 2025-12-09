# Graph Store Protocol

from pathlib import Path
from typing import Union

import httpx
from rdflib import Graph

from kurra.utils import load_graph
from .utils import rdf_suffix_map
from .sparql import query


def exists(
        sparql_endpoint: str,
        graph_iri: str,
        http_client: httpx.Client | None = None) -> bool:
    """Returns True if a graph with the given graph_iri exists at the SPARQL Endpoint or else False"""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if not graph_iri:
        raise ValueError("You must supply a graph IRI")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = httpx.head(
        f"{sparql_endpoint}",
        params={
            "graph": graph_iri,
        }
    )

    if close_http_client:
        http_client.close()

    return r.is_success


def get(
        sparql_endpoint: str,
        graph_iri: str = "default",
        content_type="text/turtle",
        http_client: httpx.Client | None = None) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP GET: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-get

    Returns the content of the graph identified by graph_id in the target SPARQL Endpoint
    as an RDFLib Graph object if it exists, or else it returns an HTTP Status Code integer."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if content_type not in rdf_suffix_map.values():
        raise ValueError(f"Media Type requested not available. Allow types are {', '.join(rdf_suffix_map.values())}")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = httpx.get(
        f"{sparql_endpoint}",
        params={
            "graph": graph_iri,
        },
        headers={
            "Accept": content_type,
        }
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return Graph().parse(data=r.text, format=content_type)
    else:
        return r.status_code


def put(
        sparql_endpoint: str,
        file_or_str_or_graph: Union[Path, str, Graph],
        graph_iri: str = "default",
        content_type="text/turtle",
        http_client: httpx.Client | None = None) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP PUT: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-put

    Inserts the RDF content supplied into a graph identified by graph_id or the default graph.

    Will replace existing content."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if content_type not in rdf_suffix_map.values():
        raise ValueError(f"Media Type requested not available. Allow types are {', '.join(rdf_suffix_map.values())}")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = httpx.put(
        f"{sparql_endpoint}",
        params={
            "graph": graph_iri,
        },
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


def post(
        sparql_endpoint: str,
        file_or_str_or_graph: Union[Path, str, Graph],
        graph_iri: str = "default",
        content_type="text/turtle",
        http_client: httpx.Client | None = None) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP POST: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-post

    Inserts the RDF content supplied into a graph identified by graph_id or the default graph.

    Will add to existing content."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if content_type not in rdf_suffix_map.values():
        raise ValueError(f"Media Type requested not available. Allow types are {', '.join(rdf_suffix_map.values())}")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = httpx.post(
        f"{sparql_endpoint}",
        params={
            "graph": graph_iri,
        },
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
        http_client: httpx.Client | None = None) -> Union[Graph, int]:
    """Graph Store Protocol's HTTP DELETE: https://www.w3.org/TR/sparql12-graph-store-protocol/#http-delete

    Deletes the graph identified by graph_id or the default graph."""
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = httpx.delete(
        f"{sparql_endpoint}",
        params={
            "graph": graph_iri,
        }
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True
    else:
        return r.status_code


def clear(
        sparql_endpoint: str,
        graph_iri: str,
        http_client: httpx.Client | None = None):
    """SPARQL Update Clear function: https://www.w3.org/TR/sparql12-update/#clear

    Clears - remove all triples from - an identified graph or from all graphs if "all" is given as the graph_id.

    This is an alias of delete()
    """
    delete(sparql_endpoint, graph_iri, http_client=http_client)


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
        return post(sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client)
    else:
        return put(sparql_endpoint, file_or_str_or_graph, graph_id, content_type, http_client)
