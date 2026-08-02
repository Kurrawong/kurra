# kurra

kurra is a Python package and command-line application for working with [RDF](https://www.w3.org/RDF/) data. It provides file conversion and 
hierarchy tools, label handling, SPARQL access, SHACL validation, Graph Store Protocol operations, and database helpers.

It is built on top of [RDFLib](https://pypi.org/project/rdflib/) and, over time, some of its functionality is likely to 
be absorbed into RDFLib.

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

Running `-h` at any level of the Command Line will print out help, e.g., for the top-level

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

For just the SPARQL function:

```bash
kurra sparql -h
```

which will print something like:

```bash                                                                                                 
Usage: kurra sparql [OPTIONS] PATH_OR_URL Q                                         
                                                                                     
 SPARQL queries to local RDF files or a database                                     
                                                                                     
╭─ Arguments ───────────────────────────────────────────────────────────────────────╮
│ *    path_or_url      PATH  [required]                                            │
│ *    q                TEXT  [required]                                            │
╰───────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────╮
│ --response-format  -f      TEXT     The response format of the SPARQL query.      │
│                                     Either 'table' (default), 'json' or 'csv'     │
│                                     [default: table]                              │
│ --username         -u      TEXT     Fuseki username.                              │
│ --password         -p      TEXT     Fuseki password.                              │
│ --timeout          -t      INTEGER  Timeout per request [default: 60]             │
│ --help             -h               Show this message and exit.                   │
╰───────────────────────────────────────────────────────────────────────────────────╯
```

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

You can also log issues at the kurra issue tracker:

* <https://github.com/Kurrawong/kurra/issues>


