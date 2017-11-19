import click

from akk import create_app
from akk.cli import fill_db_from_folders, create_base_db, download_and_extract_bpm

app = create_app("config.py")


@app.cli.command()
def create_db():
    create_base_db()


@app.cli.command()
@click.argument("song-name")
@click.argument("artist-name")
def extract_bpm(song_name, artist_name):
    bpm = download_and_extract_bpm(song_name, artist_name)
    print(bpm)


@app.cli.command()
@click.argument("base-path")
@click.argument("user")
@click.option("--no-replace/--replace")
def read_in_folders(base_path, user, no_replace):
    fill_db_from_folders(base_path, no_replace, user)


