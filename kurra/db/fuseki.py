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
):
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
):
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
):
    return server(server_url, http_client=http_client)


def stats(
    server_url: str,
    name: str = None,
    http_client: httpx.Client | None = None,
):
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
    raise NotImplementedError("backup/backups is not implemented yet")


def backups(
    server_url: str,
    name: str,
    http_client: httpx.Client | None = None,
):
    return backup(server_url, name, http_client)


def backups_list(
    server_url: str,
    http_client: httpx.Client | None = None,
):
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
    raise NotImplementedError("sleep is not implemented yet")


def tasks(
    server_url: str,
    name: str = None,
    http_client: httpx.Client | None = None,
):
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
):
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
    """
    Describe the datasetss or a single dataset in a Fuseki server instances.

    :param base_url: The base URL of the Fuseki server. E.g., http://localhost:3030
    :param dataset_name: The dataset to be described. If None (default), then all datasets will be listed
    :param http_client: The synchronous httpx client to be used. If this is not provided, a temporary one will be created.
    :raises FusekiError: If the datasets fail to list or the server responds with an invalid data structure.
    :returns: The Fuseki listing of datasets as a dictionary.
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
    """
    Delete a Fuseki dataset.

    :param base_url: The base URL of the Fuseki server. E.g., http://localhost:3030
    :param dataset_name: The dataset to be deleted
    :param http_client: The synchronous httpx client to be used. If this is not provided, a temporary one will be created.
    :raises FusekiError: If the dataset fails to delete.
    :returns: A message indicating the successful deletion of the dataset.
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
