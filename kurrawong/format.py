from pathlib import Path
from typing import Tuple

from rdflib import Graph


class FailOnChangeError(Exception):
    """
    This exception is raised when running format and the
    check bool is set to true and the file has resulted in a change.
    """


def serialize(graph: Graph) -> str:
    return graph.serialize(format="longturtle")


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


def do_format(content: str) -> Tuple[str, bool]:
    metadata = get_topbraid_metadata(content)

    graph = Graph()
    graph.parse(data=content, format="turtle")
    new_content = serialize(graph)
    new_content = metadata + new_content
    changed = content != new_content
    return new_content, changed


def format_file(
    file: Path,
    check: bool,
    output_filename: Path = None,
) -> bool:
    if not file.is_file():
        raise ValueError(f"{file} is not a file.")

    path = Path(file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path.absolute()}")

    with open(path, "r", encoding="utf-8") as fread:
        content = fread.read()

        content, changed = do_format(content)
        if changed:
            if check:
                raise FailOnChangeError(
                    f"The file {path} contains changes that can be formatted."
                )
            else:
                print(f"The file {path} has been formatted.")

            # Didn't fail and file has changed, so write to file.
            with open(
                output_filename if output_filename else path, "w", encoding="utf-8"
            ) as fwrite:
                fwrite.write(content)

    return changed


def format_rdf(path: Path, check: bool) -> None:
    path = Path(path).resolve()

    if path.is_dir():
        files = list(path.glob("**/*.ttl"))

        changed_files = []

        for file in files:
            try:
                changed = format_file(file, check)
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
            changed = format_file(path, check)
        except FailOnChangeError as err:
            print(err)
