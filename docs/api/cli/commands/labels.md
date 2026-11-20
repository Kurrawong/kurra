# Label commands

## Find duplicate names or descriptions

Use `kurra labels duplicates` with an RDF file or directory to print a table of nodes with multiple distinct annotation
literals. Names are checked by default:

```bash
kurra labels duplicates vocabulary.ttl
kurra labels duplicates vocabulary.ttl --names-or-descriptions names
```

To check descriptions instead, use `--names-or-descriptions` (short form `-n`):

```bash
kurra labels duplicates vocabulary.ttl --names-or-descriptions descriptions
kurra labels duplicates vocabulary.ttl -n descriptions
```

The only accepted annotation types are `names` and `descriptions`. Names use `schema:name`, `rdfs:label`, `dcterms:title`,
and `skos:prefLabel`; descriptions use `schema:description`, `rdfs:comment`, `dcterms:description`, and `skos:definition`.
The `schema:` predicates use the `https://schema.org/` namespace.

Supply full predicate IRIs with `--additional-annotation-predicates` (short form `-a`) to extend the default predicates.
Repeat the option for each additional IRI:

```bash
kurra labels duplicates vocabulary.ttl \
  --additional-annotation-predicates https://example.com/displayName \
  --additional-annotation-predicates https://example.com/shortName

kurra labels duplicates vocabulary.ttl -n descriptions \
  -a https://example.com/description
```

The table contains a `Node` column and a `Names` or `Descriptions` column. Literal values retain their RDF notation,
including language tags and datatypes. Identical literals under different predicates count once; differences in
spelling, datatype, or language count separately, including language versus no language. Comparisons use values as
stored by RDFLib, which may normalize typed literals when reading the source.

If no duplicates are found, the command prints `No nodes with duplicate names` or `No nodes with duplicate descriptions`.
The input file or directory must exist. For all options, run:

```bash
kurra labels duplicates --help
```

## Command reference

::: kurra.cli.commands.labels

