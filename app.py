from glob import glob

import click
import os

from akk import create_app
from akk.common.models import db
from akk.songs.functions import get_song_duration
from akk.songs.helpers import download_and_extract_bpm
from akk.songs.models import Label, Dance, Artist, Song
from akk.users.models import User

app = create_app("config.py")


@app.cli.command()
def create_db():
    """
    Convenience function to create the db file with all needed tables.
    """
    db.create_all()

    user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
    db.session.add(user)
    db.session.commit()


@app.cli.command()
@click.argument("song-name")
@click.argument("artist-name")
def test_bpm(song_name, artist_name):
    bpm = download_and_extract_bpm(song_name, artist_name)

    print(bpm)


@app.cli.command()
@click.argument("base-path")
@click.argument("user")
@click.option("--no-replace/--replace")
def read_in_hdd(base_path, user, no_replace):
    if not os.path.exists("app.db"):
        create_db()
    elif not no_replace:
        os.unlink("app.db")
        create_db()

    user = User.query.filter_by(name=user)
    if user.count() != 1:
        raise ValueError("User is not known")

    user = user.one()

    top_level_entries = [os.path.join(base_path, dir) for dir in os.listdir(base_path)]
    top_level_entries = filter(os.path.isdir, top_level_entries)

    added_counter = 0

    new_label, _ = Label.get_or_add_label("new")
    probably_wrong_label, _ = Label.get_or_add_label("probably_wrong")

    for possible_dance_dir in top_level_entries:
        possible_dance_name = os.path.split(possible_dance_dir)[-1]

        # Ask for permission
        dance_name = possible_dance_name
        dance_dir = possible_dance_dir

        dance, dance_new_created = Dance.get_or_add_dance(dance_name)

        all_songs_with_this_dance = glob(os.path.join(dance_dir, "*/*.mp3"))

        for file_name_with_this_dance in all_songs_with_this_dance:
            dance_artist_title = os.path.splitext(os.path.split(file_name_with_this_dance)[-1])[0]
            if dance_artist_title.count(" - ") != 2:
                print("File name {} in wrong format. Skipping.".format(file_name_with_this_dance))
                continue
            else:
                dance_name, artist_name, title_with_tag = dance_artist_title.split(" - ")
                artist, artist_new_created = Artist.get_or_add_artist(artist_name)

                labels = []

                if "(" in title_with_tag and title_with_tag[-1] == ")":
                    title = title_with_tag[:title_with_tag.rfind("(")]
                    label_name_string = title_with_tag[title_with_tag.rfind("(") + 1:title_with_tag.rfind(")")]
                    label_names = label_name_string.split(",")
                    labels = [Label.get_or_add_label(label_name.strip())[0] for label_name in label_names]
                else:
                    title = title_with_tag

                if "_" in title or "_" in artist.name or "_" in dance.name:
                    labels.append(probably_wrong_label)

                new_song = Song()
                new_song.title = title
                new_song.artist = artist
                new_song.dance = dance
                new_song.creation_user = user
                new_song.path = file_name_with_this_dance.replace(base_path, "")[1:]
                new_song.duration = get_song_duration(file_name_with_this_dance)

                labels.append(new_label)
                new_song.labels = labels

                db.session.add(new_song)

                added_counter += 1

            if added_counter % 10 == 0:
                print("Added", added_counter, "song to the database")

                db.session.commit()