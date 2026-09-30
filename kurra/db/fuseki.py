"""Functions to work with the Jena Fuseki RDF Database's API."""

from io import TextIOBase
from pathlib import Path

import httpx
from rdflib import RDF, Graph, URIRef


class FusekiError(Exception):
    """An error that occurred while interacting with Fuseki."""

    def __init__(self, message_context: str, message: str, status_code: int) -> None:
        self.message = f"{status_code} {message_context}. {message}"
        super().__init__(self.message)


def ping(
    server_url: str,
    http_client: httpx.Client | None = None,
) -> str:
    """Check if the Fuseki server is alive.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The server's ping response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.get(f"{server_url}/$/ping")

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to ping server at {server_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return r.text


def server(
    server_url: str,
    http_client: httpx.Client | None = None,
) -> str:
    """Get basic Fuseki server info.

    Args:
        server_url: The base URL of the Fuseki server. E.g., http://localhost:3030
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The server info response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.get(f"{server_url}/$/server")

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to get server information for server at {server_url}",
            r.text,
            r.status_code,
        )

    if close_http_client:
        http_client.close()

    return r.text


def status(
    server_url: str,
    http_client: httpx.Client | None = None,
) -> str:
    """Alias for `server()`."""
    return server(server_url, http_client=http_client)


def stats(
    server_url: str,
    name: str = None,
    http_client: httpx.Client | None = None,
) -> str:
    """Request statistics for all datasets, or one named dataset, on the Fuseki server.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        name: The dataset to get statistics for. If None (default), statistics for all datasets are returned.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The statistics response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    url = f"{server_url}/$/stats" if name is None else f"{server_url}/$/stats/{name}"
    r = http_client.get(url)

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to get stats for server at {server_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return r.text


def backup(
    server_url: str,
    name: str,
    http_client: httpx.Client | None = None,
):
    """Ask the Fuseki server to create a backup of a dataset -- Not yet implemented.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        name: The dataset to backup.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Raises:
        NotImplementedError: Not yet implemented.
    """
    raise NotImplementedError("backup/backups is not implemented yet")


def backups(
    server_url: str,
    name: str,
    http_client: httpx.Client | None = None,
):
    """Alias for `backup()`."""
    return backup(server_url, name, http_client)


def backups_list(
    server_url: str,
    http_client: httpx.Client | None = None,
) -> str:
    """List all existing backups on the Fuseki server.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The backups list response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.get(f"{server_url}/$/backups-list")

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to get stats for server at {server_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return r.text


def sleep(
    server_url: str,
    http_client: httpx.Client | None = None,
):
    """Tell the Fuseki server to sleep -- Not yet implemented.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Raises:
        NotImplementedError: Not yet implemented.
    """
    raise NotImplementedError("sleep is not implemented yet")


def tasks(
    server_url: str,
    name: str = None,
    http_client: httpx.Client | None = None,
) -> str:
    """List tasks currently running on the Fuseki server, or get one named task.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        name: The task to get. If None (default), all running tasks are listed.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The tasks response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    url = f"{server_url}/$/tasks" if name is None else f"{server_url}/$/tasks/{name}"
    r = http_client.get(url)

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to get stats for server at {server_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return r.text


def metrics(
    server_url: str,
    http_client: httpx.Client | None = None,
) -> str:
    """Get metrics for the Fuseki server.

    Args:
        server_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The metrics response text.

    Raises:
        FusekiError: If the server does not respond with success.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.get(f"{server_url}/$/metrics")

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to get stats for server at {server_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return r.text


def describe(
    base_url: str,
    dataset_name: str = None,
    http_client: httpx.Client | None = None,
) -> dict:
    """Describe the datasets on the Fuseki server, or a single named dataset.

    Args:
        base_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        dataset_name: The dataset to be described. If None (default), then all datasets will be listed.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        The Fuseki listing of datasets as a dictionary.

    Raises:
        FusekiError: If the datasets fail to list or the server responds with an invalid data structure.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    headers = {"accept": "application/json"}
    url = (
        f"{base_url}/$/datasets/{dataset_name}"
        if dataset_name is not None
        else f"{base_url}/$/datasets"
    )
    r = http_client.get(url, headers=headers)

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to list datasets at {base_url}", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    try:
        if dataset_name is None:
            return r.json()["datasets"]
        else:
            return r.json()

    except KeyError:
        raise FusekiError(
            f"Failed to parse datasets r from {base_url}",
            r.text,
            r.status_code,
        )


def create(
    sparql_endpoint: str,
    dataset_name_or_config_file: str | TextIOBase | Path,
    dataset_type: str = "tdb2",
    http_client: httpx.Client | None = None,
) -> str:
    """Create a new Fuseki dataset, from a name and type or an assembler config file.

    Args:
        sparql_endpoint: The base URL of the Fuseki server. E.g. http://localhost:3030
        dataset_name_or_config_file: The name of the dataset to create (using `dataset_type`), or an assembler config file - a path, or an open file/string of its Turtle content.
        dataset_type: The dataset type to create, when `dataset_name_or_config_file` is a name. E.g. `tdb2`.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A message confirming the dataset was created.

    Raises:
        FusekiError: If the dataset fails to create.
    """
    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    if isinstance(dataset_name_or_config_file, str):
        data = {"dbName": dataset_name_or_config_file, "dbType": dataset_type}
        r = http_client.post(f"{sparql_endpoint}/$/datasets", data=data)
        if r.status_code != 200 and r.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name_or_config_file} at {sparql_endpoint}",
                r.text,
                r.status_code,
            )
        msg = f"{dataset_name_or_config_file} created at"
    else:
        if isinstance(dataset_name_or_config_file, TextIOBase):
            data = dataset_name_or_config_file.read()
        else:
            with open(dataset_name_or_config_file, "r") as file:
                data = file.read()

        graph = Graph().parse(data=data, format="turtle")
        fuseki_service = graph.value(
            None, RDF.type, URIRef("http://jena.apache.org/fuseki#Service")
        )
        dataset_name = graph.value(
            fuseki_service, URIRef("http://jena.apache.org/fuseki#name")
        )

        r = http_client.post(
            f"{sparql_endpoint}/$/datasets",
            content=data,
            headers={"Content-Type": "text/turtle"},
        )
        status_code = r.status_code
        if r.status_code != 200 and r.status_code != 201:
            raise FusekiError(
                f"Failed to create dataset {dataset_name} at {sparql_endpoint}",
                r.text,
                status_code,
            )

        msg = f"{dataset_name} created using assembler config at"

    if close_http_client:
        http_client.close()

    return f"Dataset {msg} {sparql_endpoint}."


def delete(
    base_url: str, dataset_name: str, http_client: httpx.Client | None = None
) -> str:
    """Delete a Fuseki dataset.

    Args:
        base_url: The base URL of the Fuseki server. E.g. http://localhost:3030
        dataset_name: The dataset to be deleted.
        http_client: An optional HTTPX client to contain credentials if needed. A new one is created if not given.

    Returns:
        A message indicating the successful deletion of the dataset.

    Raises:
        FusekiError: If the dataset fails to delete.
    """
    if not dataset_name:
        raise ValueError("You must supply a dataset name")

    close_http_client = False
    if http_client is None:
        http_client = httpx.Client()
        close_http_client = True

    r = http_client.delete(f"{base_url}/$/datasets/{dataset_name}")

    if r.status_code != 200:
        raise FusekiError(
            f"Failed to delete dataset '{dataset_name}'", r.text, r.status_code
        )

    if close_http_client:
        http_client.close()

    return f"Dataset {dataset_name} deleted."
