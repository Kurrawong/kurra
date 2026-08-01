# Kurra

Kurra is a Python package and command-line application for working with RDF data.
It provides file conversion and hierarchy tools, label handling, SPARQL access,
SHACL validation, Graph Store Protocol operations, and database helpers.

## Install

```shell
pip install kurra
```

Use Kurra as a library:

```python
from kurra.file import hierarchy

hierarchy("vocabulary.ttl", use_names=True)
```

Or from the command line:

```shell
kurra file hierarchy vocabulary.ttl --use-names
```

The [API reference](api/index.md) is generated from Kurra's Python docstrings,
so it stays aligned with the installed interfaces.

