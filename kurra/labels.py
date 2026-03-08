from pathlib import Path
from typing import Literal

import httpx
from rdflib import DCTERMS, RDFS, SDO, SKOS, BNode, Graph, URIRef

from kurra.sparql import query
from kurra.utils import load_graph


def find_missing_labels(
    p: Path | str | Graph, local_context: Path | Graph = None
) -> set[URIRef]:
    """Finds all the IRIs in a graph missing labels.

    If local_context is supplied - and it must be a Path to an RDF file or directory of RDF files or a Graph - then labels from that context will be used too."""

    # find all the things missing labels
    subjects_missing_labels = set()
    predicates_missing_labels = set()
    objects_missing_labels = set()
    g = load_graph(p)

    for s in g.subjects():
        if g.value(subject=s, predicate=DCTERMS.type):
            continue
        elif g.value(subject=s, predicate=RDFS.label):
            continue
        elif g.value(subject=s, predicate=SDO.name):
            continue
        elif g.value(subject=s, predicate=SKOS.prefLabel):
            continue

        if not isinstance(s, BNode):
            subjects_missing_labels.add(s)

    for s in g.predicates():
        if g.value(subject=s, predicate=DCTERMS.type):
            continue
        elif g.value(subject=s, predicate=RDFS.label):
            continue
        elif g.value(subject=s, predicate=SDO.name):
            continue
        elif g.value(subject=s, predicate=SKOS.prefLabel):
            continue

        if not isinstance(s, BNode):
            predicates_missing_labels.add(s)

    for s in g.objects():
        if g.value(subject=s, predicate=DCTERMS.type):
            continue
        elif g.value(subject=s, predicate=RDFS.label):
            continue
        elif g.value(subject=s, predicate=SDO.name):
            continue
        elif g.value(subject=s, predicate=SKOS.prefLabel):
            continue

        if isinstance(s, URIRef):
            objects_missing_labels.add(s)

    things_missing_labels = objects_missing_labels.union(
        predicates_missing_labels.union(subjects_missing_labels)
    )

    if local_context is not None:
        tx = set()

        c = load_graph(local_context)
        for t in things_missing_labels:
            if not c.value(subject=t, predicate=SDO.name):
                tx.add(t)
        return tx
    else:
        return sorted(things_missing_labels)


def get_missing_labels(
    iris: list[URIRef],
    context: Graph | str | Path = "https://fuseki.dev.kurrawong.ai/semback/sparql",
    return_type: Literal["graph", "dict"] = "graph",
) -> Graph | dict[URIRef, str]:
    """Gets labels for given IRIs from a given context"""
    values = ""
    for i in iris:
        values += f"\t<{i}>\n"
    values = "VALUES ?iri {\n" + values + "}\n\n"

    where_clause = f"""
        WHERE {{
            {values}
            
            ?iri schema:name ?label .
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
        return query(context, q, return_format="python")
    else:
        q = f"""
            PREFIX schema: <https://schema.org/>
            
            SELECT ?iri ?label
            {where_clause}
            """
        d = {}
        for r in query(context, q, return_format="python", return_bindings_only=True):
            d[r["iri"]] = r["label"]
        return d
