import os
from glob import glob

import requests

from akk.common.models import db
from akk.songs.functions import get_or_add_label, get_or_add_dance, get_or_add_artist, get_song_duration
from akk.songs.models import Song
from akk.users.models import User


def fill_db_from_folders(base_path, no_replace, user):
    if not os.path.exists("app.db"):
        create_base_db()
    elif not no_replace:
        os.unlink("app.db")
        create_base_db()
    user = User.query.filter_by(name=user)
    if user.count() != 1:
        raise ValueError("User is not known")
    user = user.one()
    top_level_entries = [os.path.join(base_path, dir) for dir in os.listdir(base_path)]
    top_level_entries = filter(os.path.isdir, top_level_entries)
    added_counter = 0
    new_label, _ = get_or_add_label("new")
    probably_wrong_label, _ = get_or_add_label("probably_wrong")
    for possible_dance_dir in top_level_entries:
        possible_dance_name = os.path.split(possible_dance_dir)[-1]

        # Ask for permission
        dance_name = possible_dance_name
        dance_dir = possible_dance_dir

        dance, dance_new_created = get_or_add_dance(dance_name)

        all_songs_with_this_dance = glob(os.path.join(dance_dir, "*/*.mp3"))

        for file_name_with_this_dance in all_songs_with_this_dance:
            dance_artist_title = os.path.splitext(os.path.split(file_name_with_this_dance)[-1])[0]
            if dance_artist_title.count(" - ") != 2:
                print("File name {} in wrong format. Skipping.".format(file_name_with_this_dance))
                continue
            else:
                dance_name, artist_name, title_with_tag = dance_artist_title.split(" - ")
                artist, artist_new_created = get_or_add_artist(artist_name)

                labels = []

                if "(" in title_with_tag and title_with_tag[-1] == ")":
                    title = title_with_tag[:title_with_tag.rfind("(")]
                    label_name_string = title_with_tag[title_with_tag.rfind("(") + 1:title_with_tag.rfind(")")]
                    label_names = label_name_string.split(",")
                    labels = [get_or_add_label(label_name.strip())[0] for label_name in label_names]
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


def create_base_db():
    """
    Convenience function to create the db file with all needed tables.
    """
    db.create_all()
    user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
    db.session.add(user)
    db.session.commit()


def download_and_extract_bpm(song_name, artist_name):
    """
    High level function to test various websites for the given song and artist and return the first found BPM.

    :param song_name: The song name to test.
    :param artist_name: The artist name to test.
    :return: The found BPM as an integer or None.
    """
    SERVERS = [
        dict(url="https://songbpm.com/{artist_name}/{song_name}".format(
            artist_name=artist_name.replace(" ", "-").lower(),
            song_name=song_name.replace(" ", "-").lower()),
             params={}, iterator="div", class_to_look_for="number"),
        dict(url='https://www.bpmdatabase.com/music/search/',
             params={"title": song_name, "bpm": "", "genre": "", "artist": artist_name}, iterator="td",
             class_to_look_for="bpm")
    ]

    for server in SERVERS:
        bpm = _download_and_extract_bpm_with_server(server_object=server)
        if bpm:
            return bpm
    return None


def _extract_bpm(content, server_object):
    """
    Internal function to extract the BPM information from the downloaded website.
    Does this by going through the HTML tree of the site.
    :param content: The HTML content as a string.
    :param server_object: a dict with at least the keys
            * iterator: The HTML tag the BPM information is encoded in
            * class_to_look_for: the name of the HTML class, this tag has
    :return: the first found bpm or None
    """
    tree = etree.HTML(content)

    bpm = None

    for td in tree.iterfind(".//{iterator}".format(iterator=server_object["iterator"])):
        if td.get("class") and server_object["class_to_look_for"] in td.get("class").split():
            bpm = int(td.text)
            break

    return bpm


def _download_and_extract_bpm_with_server(server_object):
    """
    Do the downloading and extraction. All the information must be encoded in the server_object, which must be
    a dictionary with the keys:
    * url: the URL to download
    * params: parameters to pass to the GET of the HTML site.
    * iterator: see extract_bpm function.
    * class_to_look_for: see extract_bpm function.
    :param server_object: See above.
    :return: the extracted BPM or None.
    """
    content = requests.get(server_object["url"], params=server_object["params"]).content
    return _extract_bpm(content, server_object=server_object)