"""Functions to find RDF elements missing labels, and to acquire them from KurrawongAI's Semantic Background or another provided context."""

import re
from pathlib import Path
from typing import Iterable, Literal, cast, overload

import httpx
from rdflib import DCTERMS, RDFS, SDO, SKOS, Graph, URIRef

from kurra.sparql import query
from kurra.utils import build_values_clause, is_class, iter_iris, load_graph

# Common label predicates
LABEL_PREDICATES = [RDFS.label, SDO.name, SKOS.prefLabel, DCTERMS.title]


def find_missing_labels(
    p: Path | str | Graph, local_context: Path | Graph | None = None
) -> Iterable[URIRef]:
    """Find all the IRIs in a graph missing labels.

    Args:
        p: The RDF source to scan for IRIs missing labels as a file path, directory, RDF string, or Graph.
        local_context: An RDF file, directory, or Graph containing labels to check against, in addition to `p` itself.

    Returns:
        The IRIs missing a label.
    """

    # find all the things missing labels
    missing_labels = set()

    g = load_graph(p)

    for s in iter_iris(g):
        for node in LABEL_PREDICATES:
            if g.value(subject=s, predicate=node):
                break
        else:
            missing_labels.add(s)

    if local_context is not None:
        tx: set[URIRef] = set()

        c = load_graph(local_context)
        for t in missing_labels:
            has_context_label = any(
                c.value(subject=t, predicate=pred) for pred in LABEL_PREDICATES
            )
            if not has_context_label:
                tx.add(t)
        return tx
    else:
        return sorted(missing_labels)


@overload
def get_labels(
    iris: list[URIRef],
    context: Graph | str | Path = "https://fuseki.dev.kurrawong.ai/semback/sparql",
    return_type: Literal["graph"] = "graph",
    http_client: httpx.Client | None = None,
) -> Graph: ...


@overload
def get_labels(
    iris: list[URIRef],
    context: Graph | str | Path,
    return_type: Literal["dict"],
    http_client: httpx.Client | None = None,
) -> dict[URIRef, str]: ...


def get_labels(
    iris: list[URIRef],
    context: Graph | str | Path = "https://fuseki.dev.kurrawong.ai/semback/sparql",
    return_type: Literal["graph", "dict"] = "graph",
    http_client: httpx.Client | None = None,
) -> Graph | dict[URIRef, str]:
    """Get labels for the given IRIs from a given context, by default the KurrawongAI Semantic Background.

    Args:
        iris: The IRIs to fetch labels for.
        context: An RDF Graph, file, directory, or SPARQL endpoint containing labels to check against. Defaults to the KurrawongAI Semantic Background.
        return_type: `"graph"` to return an RDF Graph of `schema:name` labels, or `"dict"` for a dict keyed by IRI.
        http_client: An optional HTTPX client to contain credentials if needed to access a SPARQL endpoint as context. A new one is created if not given.

    Returns:
        A Graph if `return_type` is `"graph"`, or a dict of IRI to label if `"dict"`.
    """
    iri_values_clause = build_values_clause({"iri": iris})
    predicate_values_clause = build_values_clause({"pred": LABEL_PREDICATES})

    where_clause = f"""
        WHERE {{
            ?iri ?pred ?label .
            {predicate_values_clause}
            {iri_values_clause}
        }}
        """

    if return_type == "graph":
        q = f"""
            PREFIX schema: <https://schema.org/>

            CONSTRUCT {{
                ?iri schema:name ?label
            }}
            {where_clause}
            """
        return query(context, q, http_client=http_client, return_format="python")
    else:
        q = f"""
            PREFIX schema: <https://schema.org/>

            SELECT ?iri ?label
            {where_clause}
            """
        d = {}
        for r in query(
            context,
            q,
            http_client=http_client,
            return_format="python",
            return_bindings_only=True,
        ):
            d[r["iri"]] = r["label"]
        return d


SPLIT_REGEX = re.compile(
    # Split on any non-alphanumeric character
    r"[^a-zA-Z0-9]|"
    # Split on the boundary between a lowercase and uppercase letter, ie camelCase and PascalCase
    r"(?<=[a-z])(?=[A-Z])"
)


def jsonld_context(graph: Graph, vocabulary: Graph | None = None) -> dict[str, str]:
    """Create a JSON-LD context mapping resource labels to their IRIs.

    Args:
        graph: The graph to generate a context for.
        vocabulary: An additional graph to source labels and class/property types from.

    Returns:
        A dict mapping each generated JSON-LD term to its IRI.
    """
    result = {}
    all_iris = list(iter_iris(graph))
    if vocabulary is None:
        vocabulary = Graph()

    label_dict = cast(
        dict[str, str], get_labels(all_iris, vocabulary, return_type="dict")
    )
    for iri, label in label_dict.items():
        is_type = is_class(graph, URIRef(iri)) or is_class(vocabulary, URIRef(iri))

        # Create a label that is camelCase if it's a property and PascalCase if it's a class
        label_parts = [
            part.capitalize() if (i > 0 or is_type) else part
            for i, part in enumerate(SPLIT_REGEX.split(label))
        ]

        result["".join(label_parts)] = str(iri)

    return result
