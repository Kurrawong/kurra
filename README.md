# Kurrawong Python Library

A Python library of common code and CLI apps shared across Kurrawong projects and infrastructure.

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

Install the latest version of `kurra` from PyPI.

### CLI App

The recommended way to manage and run Python CLI apps is to use uv.

```bash
uv tool install kurra
```

Now you can invoke `kurra` anywhere in your terminal as long as `~/.local/bin` is in your `PATH`.

See the uv documentation on [installing tools](https://docs.astral.sh/uv/guides/tools/#installing-tools) for more information.

### Library

You can also install `kurra` as a Python library.

```bash
pip install kurra
```

Use the relevant command to add dependencies to your project if you are using a tool like uv, poetry, or conda.

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
