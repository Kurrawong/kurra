# kurra

kurra is a Python package and command-line application for working with [RDF](https://www.w3.org/RDF/) data. It provides file conversion and hierarchy tools, label handling, SPARQL access, SHACL validation, Graph Store Protocol operations, and database helpers.

It is built on top of [RDFLib](https://pypi.org/project/rdflib/) and, over time, some of its functionality is likely to be absorbed into RDFLib.

!!! note
    kurra is mainly maintained by [kurrawong.ai](https://kurrawong.ai) but is Open Source, so feel free to [contribute](#contributing)!



## Install

```shell
pip install kurra
```

## Use

Use kurra as a library:

```python
from kurra.file import hierarchy

hierarchy("vocabulary.ttl", use_names=True)
```

Or from the command line:

```shell
kurra file hierarchy vocabulary.ttl -u
```

Running `-h` at any level of the Command Line will print out help. For example, for the top-level

```bash
kurra -h
```

which will print something like:

```bash
 Usage: kurra [OPTIONS] COMMAND [ARGS]...

 Main callback for the CLI app

╭─ Options ───────────────────────────────────────────────────────────────────────────╮
│ --version  -v                                                                       │
│ --help     -h        Show this message and exit.                                    │
╰─────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────╮
│ db      RDF Database commands                                                       │
│ file    RDF file commands                                                           │
│ labels  Labelling commands                                                          │
│ shacl   SHACL commands                                                              │
│ sparql  SPARQL queries to local RDF files or a database                             │
╰─────────────────────────────────────────────────────────────────────────────────────╯
```

For SPARQL command help:

```shell
kurra sparql --help
kurra sparql query --help
kurra sparql validate --help
```

Run a query against a local file:

```shell
kurra sparql vocabulary.ttl "SELECT * WHERE { ?s ?p ?o }"
```

Validate SPARQL query or update syntax without executing it:

```shell
kurra sparql validate "SELECT * WHERE { ?s ?p ?o }"
kurra sparql validate query.sparql
```

The validator accepts inline SPARQL text or a file path. It prints `Valid SPARQL syntax` on success and reports
syntax errors with a nonzero exit status. See the [SPARQL commands](api/cli/commands/sparql.md) and
[Python API](api/sparql.md) for details.

The [API reference](api/index.md) is generated from kurra's Python docstrings, so it stays aligned with the installed interfaces.

## License

[BSD-3-Clause](https://opensource.org/license/bsd-3-clause/) license. See [the LICENSE file](https://github.com/Kurrawong/kurra/blob/main/LICENSE).

## Contributing

In the usual way on GitHub with Issues at https://github.com/Kurrawong/kurra/issues and PRs at https://github.com/Kurrawong/kurra/pulls.

## Contact & Support

kurra is maintained by:

**KurrawongAI**  
<http://kurrawong.ai>  
<info@kurrawong.ai>

Please contact them for all use & support issues.

You can also log issues at the [kurra issue tracker](https://github.com/Kurrawong/kurra/issues).
