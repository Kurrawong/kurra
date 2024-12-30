# Kurra Python Library

A Python library of RDF data manipulation functions.

## CLI Features

## `kurra format`

Format Turtle files using RDFLib's `longturtle` format.

### `kurra fuseki`

A set of commands to interface with a Fuseki server.

#### `kurra fuseki dataset list`

Get a list of Fuseki datasets.

#### `kurra fuseki dataset create`

Create a new Fuseki dataset.

#### `kurra fuseki upload`

Upload a file or a directory of files with an RDF file extension.

#### `kurra fuseki clear`

Clear a named graph or clear all graphs.

## Installation

View the [releases](https://github.com/Kurrawong/kurrawong-python/releases) page and install using the source code (zip) link.

```bash
pip install https://github.com/Kurrawong/kurra/archive/refs/tags/0.6.0.zip
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
