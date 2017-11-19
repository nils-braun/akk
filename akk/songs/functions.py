import os
import random
from datetime import timedelta, datetime

from flask import request, flash, current_app
from flask_login import current_user
from mutagen.mp3 import MP3
from sqlalchemy import not_

from akk.common.models import db
from akk.songs.constants import NOT_RATED_STRING
from akk.songs.models import Dance, Artist, Label, Rating, Comment
from .constants import SONG_PATH_FORMAT
from .models import Song, Dance, Artist, Rating, Comment, Label, LabelsToSongs


def delete_unused_old_entities(old_artist, old_dance):
    if Song.query.filter_by(artist_id=old_artist.id).count() == 0:
        db.session.delete(old_artist)

        flash(u'Deleted artist {} because no song is related any more.'.format(old_artist.name))

    if Song.query.filter_by(dance_id=old_dance.id).count() == 0:
        db.session.delete(old_dance)

        flash(u'Deleted dance {} because no song is related any more.'.format(old_dance.name))

    db.session.commit()


def delete_unused_only_labels(labels):
    for label in labels:
        related_songs_query = LabelsToSongs.query.filter_by(label_id=label.id)
        if related_songs_query.count() == 0:
            db.session.delete(label)

            flash(u'Deleted label {} because no song is related any more.'.format(label.name))

    db.session.commit()


def get_or_add_artist_and_dance(form):
    """
    Get the artist and the dance with the names form the form from the db.
    If they are not present, create new ones.
    """
    dance, dance_created_new = get_or_add_dance(form.dance_name.data)

    if dance_created_new:
        flash(u"No dance with the name {dance_name}. Created a new one.".format(dance_name=dance.name))

    artist, artist_created_new = get_or_add_artist(form.artist_name.data)

    if artist_created_new:
        flash(u"No artist with the name {artist_name}. Created a new one.".format(artist_name=artist.name))

    return artist, dance


def get_or_add_labels(form):
    labels = []
    label_names = form.labels.data.split(",")
    for label_name in label_names:
        if label_name.strip() == "":
            continue

        label, label_created_new = get_or_add_label(label_name)
        labels.append(label)

        if label_created_new:
            flash(u"No label with the name {label_name}. Created a new one.".format(label_name=label.name))

    return labels


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

    user_comment = song.get_user_comment(current_user)
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

    if not request.endpoint.startswith("wishlist."):
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
    if not request.endpoint.startswith("wishlist."):
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


def set_as_editing(song):
    song.last_edit_user = current_user
    song.last_edit_date = datetime.now()

    db.session.merge(song)
    db.session.commit()


def unset_as_editing(song):
    song.last_edit_user_id = None
    song.last_edit_date = None

    db.session.merge(song)
    db.session.commit()


def get_or_add_dance(dance_name):
    dance = Dance.query.filter_by(name=dance_name).first()
    dance_created_new = False
    if not dance:
        dance = Dance()
        dance.name=dance_name
        db.session.add(dance)
        db.session.commit()

        dance_created_new = True

    return dance, dance_created_new


def get_or_add_artist(artist_name):
    artist = Artist.query.filter_by(name=artist_name).first()
    artist_created_new = False
    if not artist:
        artist = Artist()
        artist.name=artist_name
        db.session.add(artist)
        db.session.commit()

        artist_created_new = True

    return artist, artist_created_new


def get_or_add_label(label_name):
    label = Label.query.filter_by(name=label_name).first()
    label_created_new = False
    if not label:
        label = Label()
        label.name = label_name
        label.color = random.choice(["#db56b2", "#dbc256", "#db5e56", "#91db56",
                                     "#56db7f", "#56d3db", "#566fdb", "#a056db"])
        db.session.add(label)
        db.session.commit()

        label_created_new = True

    return label, label_created_new


def get_rating(rating):
    if rating is not None:
        return "%d" % round(rating)
    else:
        return NOT_RATED_STRING


def set_add_or_delete_rating(song, user, rating_value):
    query = Rating.query.filter_by(song_id=song.id, user_id=user.id)

    if int(rating_value) != 0:
        # There is a rating
        if query.count() == 0:
            # Add new rating
            new_rating = Rating()
            new_rating.song_id = song.id
            new_rating.user_id = user.id
            new_rating.value = rating_value

            db.session.add(new_rating)
        else:
            # Update old rating
            old_rating = query.one()
            old_rating.value = rating_value
            db.session.merge(old_rating)
    else:
        if query.count() > 0:
            for rating_to_delete in query.all():
                db.session.delete(rating_to_delete)

    db.session.commit()


def set_or_add_comment(song, user, note_value):
    if note_value.strip() == "":
        # Do not add empty comments
        return

    query = Comment.query.filter_by(song_id=song.id, user_id=user.id)

    if query.count() == 0:
        # Add new rating
        new_comment = Comment()
        new_comment.song_id = song.id
        new_comment.user_id = user.id
        new_comment.creation_date = datetime.now()
        new_comment.note = note_value

        db.session.add(new_comment)
    else:
        # Update old rating
        old_comment = query.one()
        old_comment.note = note_value
        db.session.merge(old_comment)

    db.session.commit()


def get_comments_except_user(song, user):
    return Comment.query.filter(Comment.song_id == song.id, not_(Comment.user_id == user.id)).all()


def get_user_comment(song, user):
    query = Comment.query.filter_by(song_id=song.id, user_id=user.id)
    if query.count() > 0:
        return query.one()
    else:
        return None


def get_user_rating(song, user):
    query = Rating.query.filter_by(song_id=song.id, user_id=user.id)
    if query.count() > 0:
        return query.one().value
    else:
        return NOT_RATED_STRING