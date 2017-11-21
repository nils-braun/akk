import os
from datetime import timedelta, datetime

from flask import request, current_app
from flask_login import current_user
from mutagen.mp3 import MP3

from akk.common.models import db
from akk.songs.model_functions import get_or_add_artist_and_dance, get_or_add_labels, set_add_or_delete_rating, \
    set_or_add_comment, get_user_rating, delete_unused_old_entities, delete_unused_only_labels, get_user_comment
from .constants import SONG_PATH_FORMAT
from .models import Song


def get_song_duration(file_name_with_this_dance):
    audio_file = MP3(file_name_with_this_dance)
    return timedelta(seconds=audio_file.info.length)


def create_file_path(form):
    file_name = SONG_PATH_FORMAT.format(dance_name=form.dance_name.data,
                                        artist_name=form.artist_name.data,
                                        title=form.title.data)
    upload_path = os.path.join(current_app.root_path, current_app.config["DATA_FOLDER"])
    file_path_to_save_to = os.path.join(upload_path, file_name)
    return file_name, file_path_to_save_to


def set_form_from_song(song_id, form):
    song = Song.query.filter_by(id=song_id).first()

    if not song:
        return

    form.song_id.data = song_id
    form.title.data = song.title
    form.artist_name.data = song.artist.name
    form.dance_name.data = song.dance.name
    form.rating.data = get_user_rating(song, current_user)
    form.path.data = song.path
    form.bpm.data = song.bpm
    form.labels.data = ",".join(sorted([label.name for label in song.labels]))

    user_comment = get_user_comment(song, current_user)
    if user_comment:
        form.note.data = user_comment.note

    return song


def upload_file_to_song(form, song):
    uploaded_file = request.files[form.path.name]
    if uploaded_file:
        file_name, file_path_to_save_to = create_file_path(form)

        while os.path.exists(file_path_to_save_to):
            path, extension = os.path.splitext(file_path_to_save_to)
            file_path_to_save_to = path + "1" + extension

        base_path, _ = os.path.split(file_path_to_save_to)

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        uploaded_file.save(file_path_to_save_to)
        song.duration = get_song_duration(file_path_to_save_to)
        song.path = file_name

        db.session.merge(song)
        db.session.commit()


def change_or_add_song(form, song=None):
    artist, dance = get_or_add_artist_and_dance(form)

    if not request.endpoint.startswith("WishlistView:"):
        labels = get_or_add_labels(form)

    if song is None:
        song = Song(creation_user=current_user)
        song_is_new = True

        old_artist = None
        old_dance = None
        old_labels = None
    else:
        song_is_new = False

        old_artist = song.artist
        old_dance = song.dance
        # Copy is needed
        old_labels = [label for label in song.labels]

    song.artist_id = artist.id
    song.dance_id = dance.id
    song.title = form.title.data
    song.bpm = form.bpm.data

    song.last_edit_user_id = None
    song.last_edit_date = None

    if not request.endpoint.startswith("WishlistView:"):
        song.labels = labels
    else:
        song.is_on_wishlist = True

    if not song_is_new:
        db.session.merge(song)
    else:
        db.session.add(song)

    db.session.commit()

    if hasattr(form, "note"):
        set_or_add_comment(song, current_user, form.note.data)

    if hasattr(form, "rating"):
        set_add_or_delete_rating(song, current_user, form.rating.data)

    if not request.endpoint.startswith("wishlist."):
        upload_file_to_song(form, song)

    if not song_is_new:
        if artist != old_artist or dance != old_dance:
            delete_unused_old_entities(old_artist, old_dance)

        if not request.endpoint.startswith("wishlist."):
            delete_unused_only_labels(old_labels)


def add_correct_mp3_tag(f, song):
    from mutagen.easyid3 import EasyID3
    from mutagen.mp3 import MP3
    mp3_file = MP3(f.name)
    if not mp3_file.tags:
        mp3_file.add_tags()
        tags = mp3_file.tags
        tags.save(f.name)
    tag = EasyID3(f.name)
    tag["title"] = song.title
    tag["artist"] = song.artist.name
    tag["albumartist"] = song.artist.name
    if song.bpm:
        tag["bpm"] = str(song.bpm)
    tag["album"] = song.dance.name
    tag.save()