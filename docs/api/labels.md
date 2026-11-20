# Labels

## Find duplicate names or descriptions

`find_duplicate_labels()` finds nodes with more than one distinct annotation literal. It accepts a `Path`, an RDF
string, or an RDFLib `Graph`. Paths can identify an RDF file or a directory of RDF files.

By default, it checks names using `schema:name` (`https://schema.org/name`), `rdfs:label`, `dcterms:title`, and
`skos:prefLabel`. Set `names_or_descriptions="descriptions"` to check `schema:description`
(`https://schema.org/description`), `rdfs:comment`, `dcterms:description`, and `skos:definition` instead.

The result is a dictionary mapping each affected node to a set of its distinct literals across the selected predicates.
Nodes can be IRIs or blank nodes, including resources used as predicates or objects elsewhere in the graph. Identical
literals on different predicates count once. Differences in spelling, datatype, or language count separately, including
a language-tagged literal versus one without a language tag. Comparisons use the literals as stored by RDFLib, which
may normalize typed literals when loading RDF.

```python
from pathlib import Path

from rdflib import URIRef

from kurra.labels import find_duplicate_labels

source = Path("vocabulary.ttl")

# Find multiple distinct names using the default predicates.
names = find_duplicate_labels(source)

# Find multiple distinct descriptions instead.
descriptions = find_duplicate_labels(source, names_or_descriptions="descriptions")

# Extend the name predicates with additional annotation IRIs.
extra_names = find_duplicate_labels(
    source,
    additional_annotation_predicates=[
        URIRef("https://example.com/displayName"),
        URIRef("https://example.com/shortName"),
    ],
)

# Additional predicates can also extend the description predicates.
extra_descriptions = find_duplicate_labels(
    source,
    names_or_descriptions="descriptions",
    additional_annotation_predicates=[URIRef("https://example.com/description")],
)

for node, values in names.items():
    print(node.n3(), sorted(value.n3() for value in values))
```

Additional predicates supplement the defaults; they do not replace them. With no duplicates, the function returns an
empty dictionary. Values other than `"names"` or `"descriptions"` raise `ValueError`.

## API reference

::: kurra.labels

