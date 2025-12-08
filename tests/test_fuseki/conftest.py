import time
from pathlib import Path

import docker
import pytest
from testcontainers.core.container import DockerContainer

FUSEKI_IMAGE = "ghcr.io/kurrawong/fuseki-geosparql:git-main-e642d849"


def wait_for_logs(container, text, timeout=30, interval=0.5):
    """
    Wait until the container emits a log line containing `text`.
    """
    client = docker.from_env()
    start_time = time.time()

    logs_seen = ""

    while True:
        # Read logs incrementally
        logs = client.containers.get(container._container.id).logs().decode("utf-8")
        if text in logs:
            return True

        if time.time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for log: {text}")

        time.sleep(interval)


@pytest.fixture(scope="function")
def fuseki_container(request: pytest.FixtureRequest):
    container = DockerContainer(FUSEKI_IMAGE)
    container.with_volume_mapping(
        str(Path(__file__).parent / "shiro.ini"), "/fuseki/shiro.ini"
    )
    container.with_volume_mapping(
        str(Path(__file__).parent / "config.ttl"), "/fuseki/config.ttl"
    )
    container.with_exposed_ports(3030)
    container.start()
    wait_for_logs(container, "Started")

    def cleanup():
        container.stop()

    request.addfinalizer(cleanup)
    return container
