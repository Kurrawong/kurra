# Graph Store Protocol

from pathlib import Path
from typing import Union

import httpx
from rdflib import Graph

from kurra.utils import load_graph
from .fuseki.utils import FusekiError
from .utils import rdf_suffix_map


def exists(
        sparql_endpoint: str,
        graph_iri: str,
        http_client: httpx.Client | None = None) -> bool:
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
        graph_iri: str,
        content_type="text/turtle",
        http_client: httpx.Client | None = None):
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if not graph_iri:
        raise ValueError("You must supply a graph IRI")

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
        return r.text
    else:
        raise FusekiError(
            f"Failed to get graph content", r.text, r.status_code
        )


def put(
        sparql_endpoint: str,
        graph_iri: str,
        file_or_str_or_graph: Union[Path, str, Graph],
        content_type="text/turtle",
        http_client: httpx.Client | None = None):
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if not graph_iri:
        raise ValueError("You must supply a graph IRI")

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
        }
    )

    if close_http_client:
        http_client.close()

    if r.is_success:
        return True
    else:
        raise FusekiError(
            f"Failed to create/replace graph", r.text, r.status_code
        )


def clear(
        sparql_endpoint: str,
        graph_iri: str,
        http_client: httpx.Client | None = None):
    """
    Clears - remove all triples from - an identified graph or from all graphs if "all" is given as the graph_id
    """
    if not sparql_endpoint.startswith("http"):
        raise ValueError(f"SPARQL Endpoint given does not start with 'http'")

    if not graph_iri:
        raise ValueError("You must supply a graph IRI")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    query = "CLEAR ALL" if graph_iri == "all" else f"CLEAR GRAPH <{graph_iri}>"
    headers = {"content-type": "application/sparql-update"}
    r = http_client.post(sparql_endpoint, headers=headers, content=query)
    status_code = r.status_code

    if close_http_client:
        http_client.close()

    if status_code != 204:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {r.text}"
        )


def upload(
        sparql_endpoint: str,
        file_or_str_or_graph: Union[Path, str, Graph],
        graph_id: str | None = None,
        append: bool = False,
        http_client: httpx.Client | None = None,
) -> None:
    """This function uploads a file to a SPARQL Endpoint using the Graph Store Protocol.

    It will upload it into a graph identified by graph_id (an IRI or Blank Node). If no graph_id is given, it will be
    uploaded into the default graph.

    By default, it will replace all content in the Named Graph or default graph. If append is set to True, it will
    add it to existing content in the graph_id Named Graph.

    An httpx Client may be supplied for efficient client reuse, else each call to this function will recreate a new
    Client."""

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    data = load_graph(file_or_str_or_graph).serialize(format="longturtle")
    headers = {"content-type": "text/turtle"}

    if append:
        if graph_id is not None:
            response = http_client.post(sparql_endpoint, params={"graph": graph_id}, headers=headers, content=data)
        else:
            response = http_client.post(sparql_endpoint + "?default", headers=headers, content=data)
    else:
        if graph_id is not None:
            response = http_client.put(sparql_endpoint, params={"graph": graph_id}, headers=headers, content=data)
        else:
            response = http_client.put(sparql_endpoint + "?default", headers=headers, content=data)

    status_code = response.status_code

    if status_code != 200 and status_code != 201 and status_code != 204:
        message = (
            str(file_or_str_or_graph)
            if isinstance(file_or_str_or_graph, Path)
            else "content"
        )
        raise RuntimeError(
            f"Received status code {status_code} for file {message} at url {sparql_endpoint}. Message: {response.text}"
        )

    if close_http_client:
        http_client.close()
