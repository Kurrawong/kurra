from pathlib import Path

import httpx
import typer
from rich.progress import track

from kurrawong.cli.console import console
from kurrawong.fuseki import upload_file, suffix_map

app = typer.Typer()


@app.command()
def upload(
    path: Path = typer.Argument(
        ..., help="The path of a file or directory to be uploaded."
    ),
    fuseki_url: str = typer.Argument(
        ..., help="Fuseki dataset URL. E.g. http://localhost:3030/ds"
    ),
    username: str = typer.Argument(None, help="Fuseki username."),
    password: str = typer.Argument(None, help="Fuseki password."),
) -> None:
    """Upload a file or a directory of files with an RDF file extension.

    File extensions: [.nt, .nq, .ttl, .trig, .json, .jsonld, .xml]

    Files are uploaded into their own named graph in the format:
    <urn:file:{file.name}>
    E.g. <urn:file:example.ttl>
    """
    files = []

    if path.is_file():
        files.append(path)
    else:
        files += path.glob("**/*")

    auth = (
        (username, password) if username is not None and password is not None else None
    )

    files = list(filter(lambda f: f.suffix in suffix_map.keys(), files))

    with httpx.Client(auth=auth, timeout=120) as client:
        for file in track(files, description=f"Uploading {len(files)} files..."):
            try:
                upload_file(fuseki_url, file, client, f"urn:file:{file.name}")
            except Exception as err:
                console.print(
                    f"[bold red]ERROR[/bold red] Failed to upload file {file}."
                )
                raise err
