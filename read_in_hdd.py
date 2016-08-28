import os
from glob import glob

import re

import shell
from app import *

from app.songs.models import Song, Artist, Dance
from app.users.models import User

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="User name to use for filling the DB.")
    parser.add_argument("--base-path", help="Path to use for finding the files. If omitted, use the current pwd.",
                        default=os.getcwd())

    args = parser.parse_args()

    os.unlink("app.db")

    shell.create_db()

    user = User.query.filter_by(name=args.user)
    if user.count() != 1:
        raise ValueError("User is not known")

    user = user.one()

    base_path = args.base_path
    top_level_entries = [os.path.join(base_path, dir) for dir in os.listdir(base_path)]
    top_level_entries = filter(os.path.isdir, top_level_entries)


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
                dance_name, artist_name, title = dance_artist_title.split(" - ")
                artist, artist_new_created = Artist.get_or_add_artist(artist_name)

                new_song = Song(title, artist, dance, user)
                new_song.path = file_name_with_this_dance.replace(base_path, "")
                db.session.add(new_song)
                db.session.commit()

