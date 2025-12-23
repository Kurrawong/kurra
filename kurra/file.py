import itertools
from pathlib import Path
from typing import Optional, Tuple, Union

from rdflib import Dataset, Graph, URIRef

from kurra.utils import RDF_FILE_SUFFIXES, load_graph


class FailOnChangeError(Exception):
    """
    This exception is raised when running format and the
    check bool is set to true and the file has resulted in a change.
    """


def get_topbraid_metadata(content: str) -> str:
    """Get the TopBraid Composer metadata at the top of an ontology file."""
    lines = content.split("\n")
    comments = []
    for line in lines:
        if line.startswith("#"):
            comments.append(line)
        else:
            break

    if comments:
        return "\n".join(comments) + "\n"
    else:
        return ""


def do_format(
    content: str, output_format: RDF_FILE_SUFFIXES.keys() = "longturtle"
) -> Tuple[str, bool]:
    metadata = get_topbraid_metadata(content)

    graph = load_graph(content)
    new_content = graph.serialize(format=output_format, canon=True)
    new_content = metadata + new_content
    changed = content != new_content
    return new_content, changed


def _format_file(
    file: Path,
    check: bool = False,
    output_format: RDF_FILE_SUFFIXES.keys() = "longturtle",
    output_filename: Path = None,
) -> bool:
    """Inner format function - not to be used directly"""
    if not file.is_file():
        raise ValueError(f"{file} is not a file.")

    if file.suffix not in RDF_FILE_SUFFIXES.values():
        raise ValueError(
            f"File {file} is not a RDF file. Must have one of the following suffixes: {RDF_FILE_SUFFIXES.values()}"
        )

    path = Path(file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.absolute()}")

    if output_filename is None:
        output_filename = path.with_suffix(RDF_FILE_SUFFIXES[output_format])

    Path(output_filename).touch(exist_ok=True)

    with open(path, "r", encoding="utf-8") as fread:
        content = fread.read()

        content, changed = do_format(content, output_format)
        if check:
            raise FailOnChangeError(
                f"The file {path} contains changes that can be formatted."
            )
        else:
            # Didn't fail and file has changed, so write to file.
            with open(output_filename, "w", encoding="utf-8") as fwrite:
                fwrite.write(content)

    return changed


def reformat(
    path: Path,
    check: bool,
    output_format: RDF_FILE_SUFFIXES.keys() = "longturtle",
    output_filename: Path = None,
) -> None:
    """Reformats a file or all files in a given path according to the output format"""
    path = Path(path).resolve()

    if path.is_dir():
        if output_filename is not None:
            raise ValueError(
                "You cannot specify an output filename if converting multiple files"
            )

        types = [f"**/*{ft}" for ft in RDF_FILE_SUFFIXES.values()]
        files = list(
            itertools.chain.from_iterable(path.glob(pattern) for pattern in types)
        )

        changed_files = []

        for file in files:
            try:
                changed = _format_file(
                    file,
                    check,
                    output_format=output_format,
                    output_filename=output_filename,
                )
                if changed:
                    changed_files.append(file)
            except FailOnChangeError as err:
                print(err)
                changed_files.append(file)

        if check and changed_files:
            if changed_files:
                raise FailOnChangeError(
                    f"{len(changed_files)} out of {len(files)} files will change."
                )
            else:
                print(
                    f"{len(changed_files)} out of {len(files)} files will change.",
                )
        else:
            print(
                f"{len(changed_files)} out of {len(files)} files changed.",
            )
    else:
        try:
            _format_file(
                path,
                check,
                output_format=output_format,
                output_filename=output_filename,
            )
        except FailOnChangeError as err:
            print(err)


def make_dataset(
    path_str_or_graph: Union[Path, str, Graph], graph_iri: Union[str, URIRef]
) -> Dataset:
    """Returns a given Graph, or string or file of triples, as a Dataset, with the supplied graph IRI"""

    # TODO: make a Dataset from a Graph or Datatset
    # - override option to replace existing graph
    # - set default union graph
    # - set default graph
    if not isinstance(graph_iri, URIRef):
        graph_iri = URIRef(graph_iri)

    g = load_graph(path_str_or_graph)

    d = Dataset()
    for s, p, o in g:
        d.add((s, p, o, graph_iri))

    return d


def export_quads(
    path_str_or_dataset: Union[Path, str, Dataset], destination: Optional[Path] = None
) -> bool | str:
    """Exports a given Dataset, or quads in trig format or a quads file specified by a path, either as
    quads to a string, if no destination is given, or a file, if one is"""
    if isinstance(path_str_or_dataset, Path):
        d = Dataset()
        d.parse(str(path_str_or_dataset))
    elif isinstance(path_str_or_dataset, str):
        d = Dataset()
        d.parse(data=path_str_or_dataset, format="trig")
    else:  # Dataset
        d = path_str_or_dataset

    if destination is not None:
        if Path(destination).is_file():
            d2 = Dataset()
            d2.parse(destination)
            d3 = d + d2
            d3.serialize(format="trig", destination=destination)
        else:
            d.serialize(format="trig", destination=destination)

        return True
    else:
        return d.serialize(format="trig")
