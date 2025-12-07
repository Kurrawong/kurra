import json
from datetime import datetime

import pytest

from kurra.db.fuseki.admin import ping, server, status, stats, backup, backups, backups_list, sleep, tasks, metrics
from kurra.sparql import query


def test_ping(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = ping(server_url, http_client=http_client)
    assert r.startswith(str(datetime.now().year))


def test_server(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = server(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"][0]["ds.name"] == "/ds"


def test_status(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = status(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"][0]["ds.name"] == "/ds"


def test_stats(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"
    sparql_endpoint = f"http://localhost:{port}/ds"

    # bump Request up by 2
    query(sparql_endpoint, "ASK WHERE {?s ?p ?o}", http_client=http_client)
    query(sparql_endpoint, "ASK WHERE {?s ?p ?o}", http_client=http_client)

    r = stats(server_url, None, http_client=http_client)
    j = json.loads(r)
    assert j["datasets"]["/ds"]["Requests"] == 2

    # adding in the name of an existing dataset gets the same result as no name
    # adding in a non-existent name gets a 404 and no result
    r = stats(server_url, "ds", http_client=http_client)
    j = json.loads(r)
    assert j["datasets"]["/ds"]["Requests"] == 2


def test_backup(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    with pytest.raises(NotImplementedError) as e:
        backup(server_url, None, http_client=http_client)

        assert str(e) == "backup/backups is not implemented yet"


def test_backups(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    with pytest.raises(NotImplementedError) as e:
        backups(server_url, None, http_client=http_client)

        assert str(e) == "backup/backups is not implemented yet"


def test_backups_list(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = backups_list(server_url, http_client=http_client)
    j = json.loads(r)
    assert j["backups"] == []


def test_sleep(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    with pytest.raises(NotImplementedError) as e:
        sleep(server_url, http_client=http_client)

        assert str(e) == "sleep is not implemented yet"


def test_tasks(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = tasks(server_url, None, http_client=http_client)
    j = json.loads(r)
    assert j == []


def test_metrics(fuseki_container, http_client):
    port = fuseki_container.get_exposed_port(3030)
    server_url = f"http://localhost:{port}"

    r = metrics(server_url, http_client=http_client)
    assert "# HELP" in r