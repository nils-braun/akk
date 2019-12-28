import argparse
import os
from glob import glob

import shell
from app import *
from app.songs.functions import get_song_duration
from app.songs.models import Song, Artist, Dance, Label
from app.users.models import User

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="User name to use for filling the DB.")
    parser.add_argument("--base-path", help="Path to use for finding the files. If omitted, use the current pwd.",
                        default=os.getcwd())

    args = parser.parse_args()

    if not os.path.exists("app.db"):
        shell.create_db()

    base_path = args.base_path

    user = User.query.filter_by(name=args.user)
    if user.count() != 1:
        raise ValueError("User is not known")

    user = user.one()

    new_label, _ = Label.get_or_add_label("new")
    probably_wrong_label, _ = Label.get_or_add_label("probably_wrong")

    added_counter = 0

    dance_replacement = {
        "rb": "Rumba",
        "sb": "Samba",
        "qs": "Quickstep",
        "df": "Disco Fox",
        "cc": "Cha Cha",
        "sf": "Slowfox",
        "ww": "Wiener Walzer",
        "ji": "Jive",
        "tg": "Tango",
        "lw": "Langsamer Walzer",
    }

    for new_song_file in os.listdir(base_path):
        # sb - 51 - Didi - Milk & Honey - (Vol. 37, Muevete!) - CM - PP,EN.mp3
        splitted_song = new_song_file.split("-")
        assert(len(splitted_song) == 7)

        possible_dance_name = splitted_song[0].strip()
        dance_name = dance_replacement.get(possible_dance_name, possible_dance_name)
        dance, _ = Dance.get_or_add_dance(dance_name)

        bpm = int(splitted_song[1])

        title = splitted_song[2]

        artist_name = splitted_song[3]
        artist, _ = Artist.get_or_add_artist(artist_name)

        album = splitted_song[5]
        album_label, _ = Label.get_or_add_label(album)

        labels = []

        new_song = Song()
        new_song.title = title
        new_song.artist = artist
        new_song.dance = dance
        new_song.creation_user = user
        new_song.bpm = bpm
        new_song.path = os.path.join("Neue_Lieder/2019_12_01/", new_song_file)
        new_song.duration = get_song_duration(os.path.join(base_path, new_song_file))

        labels.append(new_label)
        labels.append(album_label)
        new_song.labels = labels

        db.session.add(new_song)

        added_counter += 1

        if added_counter % 10 == 0:
            print("Added", added_counter, "song to the database")

    #db.session.commit()

