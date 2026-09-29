"""Formatting helpers that convert SPARQL and SHACL results into CLI-friendly output."""

import csv
import datetime
import io
import json
from decimal import Decimal

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, SH
from rdflib.plugins.sparql.processor import SPARQLResult
from rich.table import Table

from kurra.utils import is_construct_or_describe_query

EX = Namespace("http://example.com/")


def format_sparql_response_as_rich_table(
    response: SPARQLResult | Graph | dict, query: str
) -> Table | str:
    """Format a SPARQL query result for terminal display using print.

    CONSTRUCT/DESCRIBE results and RDF graphs are serialized as longturtle, SELECT and ASK results are rendered as a Rich table.

    Args:
        response: The parsed SPARQL response - an rdflib `SPARQLResult`, an rdflib `Graph`, or a dict of raw JSON results.
        query: The original SPARQL query string, used for determining query type.

    Returns:
        A Rich `Table` for SELECT/ASK results, or a longturtle-serialized string for CONSTRUCT/DESCRIBE/graph results.
    """
    if is_construct_or_describe_query(query):
        return response.serialize(format="longturtle")

    if isinstance(response, Graph):
        return response.serialize(format="longturtle")

    t = Table()

    # ASK
    if not response.get("results"):
        t.add_column("Ask")
        t.add_row(str(response["boolean"]))
    else:  # SELECT
        for x in response["head"]["vars"]:
            t.add_column(x)
        for row in response["results"]["bindings"]:
            cols = []
            for k, v in {
                key: row[key] for key in response["head"]["vars"] if key in row
            }.items():
                cols.append(str(v))
            t.add_row(*tuple(cols))

    return t


def format_sparql_response_as_json(response: SPARQLResult | dict) -> str:
    """Serialize a SPARQL query result to a JSON string.

    Args:
        response: The parsed SPARQL response - either an rdflib `SPARQLResult` or an already-decoded JSON-compatible dict.

    Raises:
        TypeError: If a value in the response cannot be converted to a JSON-serializable or RDF literal form.

    Returns:
        A JSON-formatted string of the response.
    """
    if isinstance(response, SPARQLResult):
        response = json.loads(response.serialize(format="json").decode())

    def rdf_literal_to_json(value):
        if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)

        # RDFLib uses additional Python types for literals such as xsd:duration.
        # Converting them back to a Literal produces their canonical RDF lexical
        # form, which is safe to represent as a JSON string.
        try:
            literal = Literal(value)
            if literal.datatype is not None:
                return str(literal)
        except (TypeError, ValueError):
            pass

        raise TypeError(
            f"Object of type {type(value).__name__} is not JSON serializable"
        )

    return json.dumps(
        response,
        default=rdf_literal_to_json,
        ensure_ascii=False,
        indent=4,
    )


def format_sparql_response_as_csv(
    response: SPARQLResult | Graph | dict, query: str
) -> str:
    """Format a SPARQL query result as CSV.

    CONSTRUCT/DESCRIBE results and RDF graphs are serialized as longturtle instead of CSV, since they aren't tabular.

    Args:
        response: The parsed SPARQL response - an rdflib `SPARQLResult`, an rdflib `Graph`, or a dict of raw JSON results.
        query: The original SPARQL query string, used for determining query type.

    Returns:
        A CSV-formatted string for SELECT/ASK results, or a longturtle-serialized string for CONSTRUCT/DESCRIBE/graph results.
    """
    if is_construct_or_describe_query(query):
        return response.serialize(format="longturtle")

    if isinstance(response, Graph):
        return response.serialize(format="longturtle")

    s = io.StringIO()
    writer = csv.writer(s)

    # ASK
    if not response.get("results"):
        writer.writerow("Ask")
    else:  # SELECT
        writer.writerow(response["head"]["vars"])

        for row in response["results"]["bindings"]:
            r = []
            for k, v in {
                key: row[key] for key in response["head"]["vars"] if key in row
            }.items():
                r.append(str(v))
            writer.writerow(r)

    return s.getvalue()


def format_shacl_graph_as_rich_table(g: Graph) -> Table:
    """Build a Rich table of SHACL validation results.

    Args:
        g: An RDF graph containing SHACL `sh:ValidationResult` nodes.

    Returns:
        A Rich `Table` listing each validation error's focus node and message.
    """
    t = Table(padding=(1, 0))
    t.add_column("No.")
    t.add_column("Error")
    t.add_column("Message")
    errs = 0
    for vr in g.subjects(RDF.type, SH.ValidationResult):
        errs += 1
        t.add_row(
            str(errs),
            g.value(vr, SH.focusNode),
            g.value(vr, SH.resultMessage),
        )

    return t


def format_shacl_summary_as_rich_table(g: Graph) -> Table:
    """Build a Rich table summarizing SHACL validation results by shape.

    Args:
        g: An RDF graph containing a SHACL validation summary report (`ValidationReportSummary` and `ValidationResultSummary` nodes).

    Returns:
        A Rich `Table`, titled with the total violation/warning/info counts, with one row per shape summary.
    """
    counts = g.value(
        subject=g.value(predicate=RDF.type, object=EX.ValidationReportSummary),
        predicate=EX["counts"],
    )
    violations = g.value(counts, EX.violationCount, default=Literal(0))
    warnings = g.value(counts, EX.warningCount, default=Literal(0))
    info = g.value(counts, EX.infoCount, default=Literal(0))

    t = Table(
        title=(
            f"Validation summary — Violations: {violations}, "
            f"Warnings: {warnings}, Info: {info}"
        ),
        padding=(1, 0),
    )
    t.add_column("No.")
    t.add_column("Shape")
    t.add_column("Count")
    t.add_column("Message")
    t.add_column("Example node")

    summaries = sorted(
        g.subjects(RDF.type, EX.ValidationResultSummary),
        key=lambda result: str(g.value(result, SH.sourceShape)),
    )
    for number, result in enumerate(summaries, start=1):
        t.add_row(
            str(number),
            g.value(result, SH.sourceShape),
            g.value(result, EX["count"]),
            g.value(result, SH.resultMessage),
            g.value(result, EX.exampleNode),
        )

    return t
