from unittest.mock import patch

import httpx
import pytest
from pyparsing import ParseBaseException
from rdflib import Graph
from sparqlib import SparqlSyntaxError
from typer.testing import CliRunner

from kurra.cli import app
from kurra.db.sparql import query as remote_query
from kurra.sparql import query, validate


@pytest.mark.parametrize(
    "q",
    [
        "SELECT * WHERE { ?s ?p ?o }",
        "ASK { ?s ?p ?o }",
        "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }",
        "INSERT DATA { <urn:s> <urn:p> <urn:o> }",
        "DELETE WHERE { ?s ?p ?o }; CLEAR ALL",
        "# update\nPREFIX ex: <urn:> INSERT DATA { ex:s ex:p ex:o }",
    ],
)
def test_validate(q):
    assert validate(q) is None


@pytest.mark.parametrize("q", ["SELECT WHERE {", "INSERT DATA {", "nonsense"])
def test_invalid(q):
    with pytest.raises(ParseBaseException):
        validate(q)


def test_validate_file(tmp_path):
    path = tmp_path / "query.sparql"
    path.write_text("SELECT * WHERE { ?s ?p ?o }")
    validate(path)
    validate(str(path))


@pytest.mark.parametrize("call", [query, remote_query])
@pytest.mark.parametrize("q", ["SELECT WHERE {", "INSERT DATA {"])
def test_remote_rejected_before_request(call, q):
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: pytest.fail("HTTP sent"))
    ) as client:
        with pytest.raises((ParseBaseException, SparqlSyntaxError)):
            call("https://example.com/sparql", q, http_client=client)


def test_remote_validates_after_namespaces():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"head": {}, "boolean": True})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        query(
            "https://example.com/sparql",
            "ASK { ex:s ex:p ex:o }",
            namespaces={"ex": "urn:"},
            http_client=client,
        )
    assert len(requests) == 1


def test_local_does_not_call_validate():
    with patch("kurra.sparql.validate", side_effect=AssertionError("extra parsing")):
        query(Graph(), "ASK { ?s ?p ?o }")
        query(Graph(), "INSERT DATA { <urn:s> <urn:p> <urn:o> }")


@pytest.mark.parametrize("q", ["ASK { ?s ?p ?o }", "CLEAR ALL"])
def test_cli_validate(q):
    result = CliRunner().invoke(app, ["sparql", "validate", q])
    assert result.exit_code == 0, result.output
    assert "Valid SPARQL syntax" in result.output


def test_cli_validate_file(tmp_path):
    path = tmp_path / "query.sparql"
    path.write_text("ASK { ?s ?p ?o }")
    result = CliRunner().invoke(app, ["sparql", "validate", str(path)])
    assert result.exit_code == 0, result.output


def test_cli_invalid():
    result = CliRunner().invoke(app, ["sparql", "validate", "SELECT WHERE {"])
    assert result.exit_code != 0
    assert "Invalid SPARQL syntax at line" in result.output


@pytest.mark.parametrize("call", [query, remote_query])
@pytest.mark.parametrize(
    "q",
    [
        "ASK { ?s ?p ?o }",
        "INSERT DATA { <urn:s> <urn:p> <urn:o> }",
    ],
)
def test_remote_calls_validate_once(call, q):
    with (
        httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, text=""))
        ) as client,
        patch("kurra.sparql.validate", wraps=validate) as validator,
    ):
        call("https://example.com/sparql", q, http_client=client)
    validator.assert_called_once_with(q)
