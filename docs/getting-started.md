# Getting started

## Python

Kurra accepts RDFLib graphs, RDF content, paths, and—in supported operations—HTTP
URLs. The API reference describes the accepted inputs for each function.

```python
from pathlib import Path

from kurra.file import hierarchy, merge

merge(Path("first.ttl"), Path("second.ttl"), destination=Path("merged.ttl"))
hierarchy(Path("merged.ttl"), use_names=True)
```

## Command line

Install the package and inspect the available command groups:

```shell
kurra --help
kurra file --help
kurra db --help
```

For authoritative parameter and return-value details, see the
[API reference](api/index.md), which is rendered directly from source docstrings.

