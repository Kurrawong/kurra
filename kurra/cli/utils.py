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


def format_sparql_response_as_rich_table(response, query):
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


def format_sparql_response_as_json(response):
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


def format_sparql_response_as_csv(response, query):
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


def format_shacl_graph_as_rich_table(g: Graph):
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


def format_shacl_summary_as_rich_table(g: Graph):
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
