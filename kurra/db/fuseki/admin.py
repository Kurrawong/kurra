import httpx

from ..utils import FusekiError


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
            f"Failed to get server information for server at {server_url}", r.text, r.status_code
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