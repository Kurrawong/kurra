# Kurra Python Library

A Python library of RDF data manipulation functions.

This library uses the [RDFLib](https://pypi.org/project/rdflib/) under-the-hood to process 
[RDF](https://www.w3.org/RDF/) data and supplies functions to:

* upload it to RDF databases - "triplestores" - and query them
* manipulate it in a few commands - e.g. format conversion

This toolkit provides a command line interface (CLI) for doing all of this as well as presenting its functions in a 
library that other Python applications can use.


## Command Line Interface

kurra uses a Command Line Interface that can be inspected. Once you have installed kurra (see below), you can ask it to
tell you want commands it supports with `--help`, e.g.:

```bash
kurra --help
```

which will return something like:

╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                         │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.  │
│ --help                        Show this message and exit.                                                       │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ list      Get a list of Fuseki datasets                                                                         │
│ create    Create a new Fuseki dataset                                                                           │
│ query     Query a Fuseki database                                                                               │
│ upload    Upload files to a Fuseki dataset.                                                                     │
│ format    Format RDF files using one of several common RDF formats.                                             │
│ version   Show the version of the kurra app.                                                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

You can then run 

```bash
kurra format --help
```

or

```bash
kurra create --help
```

etc. to get further help for the particular commands.


## Installation

For use as a Python library, simple installation from PIP/Poetry:

```bash
pip install kurra
```

```bash
poetry add kurra
```

Then import it and use in your code, e.g. for the format functions:

```bash
from kurra.format import format_file, make_dataset, export_quads
```



## Development

Install the Poetry project and its dependencies.

```bash
task install
```

Format code.

```bash
task code
```

## License

[BSD-3-Clause](https://opensource.org/license/bsd-3-clause/) license. See [LICENSE](LICENSE).
