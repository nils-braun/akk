import random
from datetime import datetime

from flask import flash
from sqlalchemy import not_

from akk.common.models import db
from akk.songs.constants import NOT_RATED_STRING
from akk.songs.models import Dance, Artist, Label, Rating, Comment, Song, LabelsToSongs


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