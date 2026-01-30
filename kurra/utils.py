import json
import pickle
from enum import Enum
from pathlib import Path
from typing import Union

import httpx
from rdflib import BNode, Dataset, Graph, Literal, Namespace, URIRef
from rdflib.plugins.parsers.notation3 import BadSyntax
from sparqlkit import (
    QuerySubType,
    SparqlStatementType,
    SparqlType,
    UpdateSubType,
    statement_type_from_string,
)

RDF_SUFFIX_MAP = {
    ".nt": "application/n-triples",
    ".nq": "application/n-quads",
    ".owl": "application/rdf+xml",
    ".ttl": "text/turtle",
    ".trig": "application/trig",
    ".json": "application/ld+json",
    ".jsonld": "application/ld+json",
    ".xml": "application/rdf+xml",
}

RDF_FILE_SUFFIXES = {
    "turtle": ".ttl",
    "longturtle": ".ttl",
    "xml": ".rdf",
    "n-triples": ".nt",
    "json-ld": ".jsonld",
    "owl": ".owl",
}

SYSTEM_GRAPH_IRI = URIRef("https://olis.dev/SystemGraph")

OLIS = Namespace("https://olis.dev/")


class RenderFormat(str, Enum):
    original = "original"
    json = "json"
    markdown = "markdown"


def guess_format_from_data(rdf: str) -> str | None:
    if rdf is not None:
        rdf = rdf.strip()
        if rdf.startswith("PREFIX") or rdf.startswith("@prefix"):
            return "text/turtle"
        elif rdf.startswith("{") or rdf.startswith("["):
            return "application/ld+json"
        elif rdf.startswith("<?xml") or rdf.startswith("<rdf"):
            return "application/rdf+xml"
        elif rdf.startswith("<http"):
            return "application/n-triples"
        else:
            return "application/n-triples"
    else:
        return None


def load_graph(graph_path_or_str: Union[Graph, Path, str], recursive=False) -> Graph:
    """
    Presents an RDFLib Graph object from a pre-existing Graph, a pickle file, an RDF file or directory of files or RDF
    data in a string
    """
    # Pre-existing Graph
    if isinstance(graph_path_or_str, Graph):
        return graph_path_or_str

    # Pickle file
    if isinstance(graph_path_or_str, Path):
        if graph_path_or_str.is_file():
            pkl_path = graph_path_or_str.with_suffix(".pkl")
            if pkl_path.is_file():
                return pickle.load(open(pkl_path, "rb"))

    # Serialized RDF file or dir of files
    if isinstance(graph_path_or_str, Path):
        if Path(graph_path_or_str).is_file():
            if str(graph_path_or_str).endswith(".trig") or str(
                graph_path_or_str
            ).endswith(".jsonld"):
                return Dataset().parse(str(graph_path_or_str))
            return Graph().parse(graph_path_or_str)
        elif Path(graph_path_or_str).is_dir():
            g = Graph()
            if recursive:
                gl = Path(graph_path_or_str).rglob("*.ttl")
            else:
                gl = Path(graph_path_or_str).glob("*.ttl")
            for f in gl:
                if f.is_file():
                    g.parse(f)
            return g

    # A remote file via HTTP
    elif isinstance(graph_path_or_str, str) and graph_path_or_str.startswith("http"):
        return Graph().parse(graph_path_or_str)

    # RDF data in a string
    else:
        return Graph().parse(
            data=graph_path_or_str,
            format=guess_format_from_data(graph_path_or_str),
        )


def render_sparql_result(
    r: dict | str | Graph, rf: RenderFormat = RenderFormat.markdown
) -> str:
    """Renders a SPARQL result in a given render format"""
    if rf == RenderFormat.original:
        return r

    elif rf == RenderFormat.json:
        if isinstance(r, dict):
            return json.dumps(r, indent=4)
        elif isinstance(r, str):
            return json.dumps(json.loads(r), indent=4)
        elif isinstance(r, Graph):
            return r.serialize(format="json-ld", indent=4)

    elif rf == RenderFormat.markdown:
        if isinstance(r, Graph):  # CONSTRUCT: RDF GRaph
            output = "```turtle\n" + r.serialize(format="longturtle") + "```\n"
        else:  # SELECT or ASK: Python dict or JSON

            def render_sparql_value(v: dict) -> str:
                # TODO: handle v["datatype"]
                if v is None:
                    return ""
                elif isinstance(v, URIRef) or isinstance(v, str):
                    return f"[{v.split('/')[-1].split('#')[-1]}]({v})"
                elif isinstance(v, Literal):
                    return v
                elif isinstance(v, BNode):
                    return f"BN: {v:>6}"
                elif v["type"] == "uri":
                    return f"[{v['value'].split('/')[-1].split('#')[-1]}]({v['value']})"
                elif v["type"] == "literal":
                    return v["value"]
                elif v["type"] == "bnode":
                    return f"BN: {v['value']:>6}"

            if isinstance(r, str):
                r = json.loads(r)

            output = ""
            header = ["", ""]
            body = []

            if r.get("head") is not None:
                # SELECT
                if r["head"].get("vars") is not None:
                    for col in r["head"]["vars"]:
                        header[0] += f"{col} | "
                        header[1] += f"--- | "
                    output = (
                        "| " + header[0].strip() + "\n| " + header[1].strip() + "\n"
                    )

            if r.get("results"):
                if r["results"].get("bindings"):
                    for row in r["results"]["bindings"]:
                        row_cols = []
                        for k in r["head"]["vars"]:
                            v = row.get(k)
                            if v is not None:
                                # ignore the k
                                row_cols.append(render_sparql_value(v))
                            else:
                                row_cols.append("")
                        body.append(" | ".join(row_cols))

                output += "\n| ".join(body) + " |\n"

            if r.get("boolean") is not None:
                output = str(bool(r.get("boolean")))

        return output


def make_httpx_client(
    sparql_username: str = None,
    sparql_password: str = None,
):
    auth = None
    if sparql_username:
        if sparql_password:
            auth = httpx.BasicAuth(sparql_username, sparql_password)
    return httpx.Client(auth=auth)


def convert_sparql_json_to_python(
    j: Union[str, bytes, httpx.Response], return_bindings_only=False
) -> {}:
    if type(j) == str:
        r = json.loads(j)
    elif type(j) == bytes:
        r = json.loads(j.decode())
    elif type(j) == httpx.Response:
        r = j.json()

    if r.get("results") is not None:  # SELECT
        for row in r["results"]["bindings"]:
            for k, v in row.items():
                if v["type"] == "literal":
                    if v.get("datatype") is not None:
                        row[k] = Literal(v["value"], datatype=v["datatype"]).toPython()
                    else:
                        row[k] = Literal(v["value"]).toPython()
                elif v["type"] == "uri":
                    row[k] = v["value"]
        if return_bindings_only:
            r = r["results"]["bindings"]
        return r
    elif r.get("boolean") is not None:  # ASK
        if return_bindings_only:
            return bool(r["boolean"])
        else:
            return r
    else:
        return r


def sparql_statement_return_type(
    query: str, statement: SparqlStatementType | None = None
) -> str:
    statement = _ensure_statement_type(query, statement)
    if is_construct_or_describe_query(query, statement):
        return "text/turtle"
    return "application/sparql-results+json"


def statement_type_for_query(query: str) -> SparqlStatementType:
    return statement_type_from_string(query)


def _ensure_statement_type(
    query: str, statement: SparqlStatementType | None = None
) -> SparqlStatementType:
    return statement if statement is not None else statement_type_for_query(query)


def is_construct_query(
    query: str, statement: SparqlStatementType | None = None
) -> bool:
    statement = _ensure_statement_type(query, statement)
    return (
        statement.type == SparqlType.QUERY
        and statement.subtype == QuerySubType.CONSTRUCT
    )


def is_describe_query(query: str, statement: SparqlStatementType | None = None) -> bool:
    statement = _ensure_statement_type(query, statement)
    return (
        statement.type == SparqlType.QUERY
        and statement.subtype == QuerySubType.DESCRIBE
    )


def is_select_query(query: str, statement: SparqlStatementType | None = None) -> bool:
    statement = _ensure_statement_type(query, statement)
    return (
        statement.type == SparqlType.QUERY and statement.subtype == QuerySubType.SELECT
    )


def is_ask_query(query: str, statement: SparqlStatementType | None = None) -> bool:
    statement = _ensure_statement_type(query, statement)
    return statement.type == SparqlType.QUERY and statement.subtype == QuerySubType.ASK


def is_construct_or_describe_query(
    query: str, statement: SparqlStatementType | None = None
) -> bool:
    statement = _ensure_statement_type(query, statement)
    return statement.type == SparqlType.QUERY and statement.subtype in {
        QuerySubType.CONSTRUCT,
        QuerySubType.DESCRIBE,
    }


def is_select_or_ask_query(
    query: str, statement: SparqlStatementType | None = None
) -> bool:
    statement = _ensure_statement_type(query, statement)
    return statement.type == SparqlType.QUERY and statement.subtype in {
        QuerySubType.SELECT,
        QuerySubType.ASK,
    }


def is_update_query(query: str, statement: SparqlStatementType | None = None) -> bool:
    statement = _ensure_statement_type(query, statement)
    return statement.type == SparqlType.UPDATE


def is_drop_update(query: str, statement: SparqlStatementType | None = None) -> bool:
    statement = _ensure_statement_type(query, statement)
    return (
        statement.type == SparqlType.UPDATE and statement.subtype == UpdateSubType.DROP
    )


def make_sparql_dataframe(sparql_result: dict):
    try:
        from pandas import DataFrame
    except ImportError:
        raise ValueError(
            'You selected the output format "dataframe" but the pandas Python package is not installed.'
        )

    if sparql_result.get("results") is not None:  # SELECT
        df = DataFrame(columns=sparql_result["head"]["vars"])
        for i, row in enumerate(sparql_result["results"]["bindings"]):
            new_row = {}
            for k, v in row.items():
                if v["type"] == "literal":
                    if v.get("datatype") is not None:
                        new_row[k] = Literal(
                            v["value"], datatype=v["datatype"]
                        ).toPython()
                    else:
                        new_row[k] = Literal(v["value"]).toPython()
                else:
                    new_row[k] = v["value"]
            df.loc[i] = new_row
        return df
    else:  # ASK
        df = DataFrame(columns=["boolean"])
        df.loc[0] = sparql_result["boolean"]

    return df


def add_namespaces_to_query_or_data(q: str, namespaces: dict):
    preamble = ""
    for k, v in namespaces.items():
        preamble += f"PREFIX {k}: <{v}>\n"
    preamble += "\n"
    return preamble + q


def make_httpx_client(
    sparql_username: str = None,
    sparql_password: str = None,
    timeout: int = 60,
):
    auth = None
    if sparql_username:
        if sparql_password:
            auth = httpx.BasicAuth(sparql_username, sparql_password)
    return httpx.Client(auth=auth, timeout=timeout)


def get_system_graph(
    system_graph_source: str | Path | Dataset | Graph = None,
    http_client: httpx.Client | None = None,
):
    """Returns a System Graph, graph and can accept many source options"""
    system_graph = Graph(identifier=SYSTEM_GRAPH_IRI)
    system_graph.bind("olis", OLIS)
    if system_graph_source is None:
        # no incoming System Graph
        pass
    elif isinstance(system_graph_source, Path):
        # we have a Graph or Dataset file, so read it
        if not system_graph_source.is_file():
            raise ValueError(
                f"system_graph_source must be an existing RDF file. Value supplied was {system_graph_source}"
            )

        if system_graph_source.suffix == ".trig":
            system_graph += (
                Dataset()
                .parse(system_graph_source, format="trig")
                .get_graph(SYSTEM_GRAPH_IRI)
            )
        else:
            system_graph += load_graph(system_graph_source)
    elif isinstance(system_graph_source, Graph):
        # we have a Graph, so assume it's a System Graph and load it
        system_graph += system_graph_source
    elif isinstance(system_graph_source, Dataset):
        # we have a Dataset object, so load its system Graph
        system_graph += system_graph_source.get_graph(str(SYSTEM_GRAPH_IRI))
    elif system_graph_source and system_graph_source.startswith("http"):
        # we have a remote SPARQL Endpoint, so read the System Graph
        # this is simplified GSP get()
        close_http_client = False
        if http_client is None:
            http_client = httpx.Client()
            close_http_client = True

        r = http_client.get(
            str(system_graph_source),
            params={"graph": SYSTEM_GRAPH_IRI},
            headers={"Accept": "text/turtle"},
        )

        if close_http_client:
            http_client.close()

        if r.is_success:
            system_graph += Graph().parse(data=r.text, format="turtle")
        else:
            return r.status_code
    elif system_graph_source and not system_graph_source.startswith("http"):
        system_graph += load_graph(system_graph_source)
    else:
        raise ValueError(
            "The parameter system_graph_source must be either None, a Path to an RDF Graph or Dataset serialised "
            "in Turtle or Trig, an RDFLib Graph object assumed to be a System Graph, an RDFLib Dataset object containing"
            "a System Graph or a string URL for a SPARQL Endpoint."
        )

    return system_graph


def put_system_graph(
    system_graph: Graph,
    system_graph_source: str | Path | Dataset | Graph = None,
    http_client: httpx.Client | None = None,
):
    if system_graph_source is None:
        return system_graph
    elif isinstance(system_graph_source, Path):
        if system_graph_source.suffix == ".trig":
            # TODO: deduplicate the Dataset parse in get_system_graph
            d = Dataset().parse(system_graph_source, format="trig")
            d.remove_graph(SYSTEM_GRAPH_IRI)
            d.add_graph(system_graph)
            d.serialize(destination=system_graph_source, format="trig")
        else:
            system_graph.serialize(destination=system_graph_source, format="longturtle")

        return None
    elif isinstance(system_graph_source, Graph):
        system_graph_source = system_graph
        return None
    elif isinstance(system_graph_source, Dataset):
        system_graph_source.remove_graph(SYSTEM_GRAPH_IRI)
        system_graph_source.add_graph(system_graph)
        return None
    elif system_graph_source and system_graph_source.startswith("http"):
        # this is simplified GSP put()
        close_http_client = False
        if http_client is None:
            http_client = httpx.Client()
            close_http_client = True

        r = http_client.put(
            system_graph_source,
            params={"graph": SYSTEM_GRAPH_IRI},
            headers={"Content-Type": "text/turtle"},
            content=system_graph.serialize(format="text/turtle"),
        )

        if close_http_client:
            http_client.close()

        if r.is_success:
            return None
        else:
            return r.status_code
    elif system_graph_source and not system_graph_source.startswith("http"):
        return system_graph
    else:
        return None
