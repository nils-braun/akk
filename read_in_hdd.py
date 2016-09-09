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
    parser.add_argument("--no-replace", help="Do not replace the old database file.", action="store_true")

    args = parser.parse_args()

    if not os.path.exists("app.db"):
        shell.create_db()
    elif not args.no_replace:
        os.unlink("app.db")
        shell.create_db()

    user = User.query.filter_by(name=args.user)
    if user.count() != 1:
        raise ValueError("User is not known")

    user = user.one()

    base_path = args.base_path
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

