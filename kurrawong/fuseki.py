import json
from pathlib import Path

import httpx

suffix_map = {
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".ttl": "text/turtle",
    ".trig": "application/trig",
    ".json": "application/ld+json",
    ".jsonld": "application/ld+json",
    ".xml": "application/rdf+xml",
}


def upload_file(
    url: str,
    file: Path,
    http_client: httpx.Client,
    graph_name: str = None,
) -> None:
    params = {"graph": graph_name} if graph_name else None

    headers = {"content-type": suffix_map[file.suffix]}
    with open(file, "r", encoding="utf-8") as f:
        data = f.read()
        response = http_client.put(url, params=params, headers=headers, data=data)
        status_code = response.status_code

        if status_code != 200 and status_code != 201 and status_code != 204:
            raise RuntimeError(
                f"Received status code {status_code} for file {file} at url {url}. Message: {response.text}"
            )


def dataset_list(
    url: str,
    http_client: httpx.Client,
) -> str:
    headers = {"accept": "application/json"}
    response = http_client.get(f"{url}/$/datasets", headers=headers)
    status_code = response.status_code

    if status_code != 200:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )

    return json.dumps(response.json(), indent=2)


def dataset_create(
    url: str, http_client: httpx.Client, dataset_name: str, dataset_type: str = "tdb2"
) -> str:
    data = {"dbName": dataset_name, "dbType": dataset_type}
    response = http_client.post(f"{url}/$/datasets", data=data)
    status_code = response.status_code

    if response.status_code != 200 and response.status_code != 201:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )

    return f"Dataset {dataset_name} created at {url}."


def dataset_clear(url: str, http_client: httpx.Client, named_graph: str):
    query = (
        "CLEAR ALL" if named_graph == "all" else f"CLEAR GRAPH <{named_graph}>"
    )
    headers = {"content-type": "application/sparql-update"}
    response = http_client.post(url, headers=headers, content=query)
    status_code = response.status_code

    if status_code != 204:
        raise RuntimeError(
            f"Received status code {status_code}. Message: {response.text}"
        )
