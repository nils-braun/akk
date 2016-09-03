import os
from datetime import timedelta

from flask import request, flash, url_for, g
from mutagen.mp3 import MP3

from app import db, app
from app.functions import render_template_with_user, get_redirect_target, redirect_back_or
from app.songs.constants import SONG_PATH_FORMAT
from app.songs.models import Song, Dance, Artist, Rating, Comment


def delete_entity(FormClass, DataClass, name, song_argument):
    form = FormClass(request.values)
    next_url = get_redirect_target()

    data_to_delete = []
    if form.validate_on_submit():
        entity = DataClass.query.filter_by(name=form.name.data).first()
        if entity:
            filter_dict = {song_argument: entity.id}
            data_to_delete = Song.query.filter_by(**filter_dict).all()

            if form.sure_to_delete.data:

                old_artists_and_dances = [(song.artist, song.dance) for song in data_to_delete]

                db.session.delete(entity)
                db.session.commit()

                for artist, dance in old_artists_and_dances:
                    delete_unused_old_entities(artist, dance)

                flash('Sucessfully deleted %s' % entity.name)
                return redirect_back_or(url_for('songs.home'))
            else:
                flash('Are you sure you want to delete?')
                form.sure_to_delete.data = True

        else:
            flash('No %s with this name' % name, 'error-message')
    return render_template_with_user("songs/deletion_form.html", form=form, data_to_delete=data_to_delete, next=next_url)


def delete_unused_old_entities(old_artist, old_dance):
    if Song.query.filter_by(artist_id=old_artist.id).count() == 0:
        db.session.delete(old_artist)
        db.session.commit()

        flash('Deleted artist {} because no song is related any more.'.format(old_artist.name))

    if Song.query.filter_by(dance_id=old_dance.id).count() == 0:
        db.session.delete(old_dance)
        db.session.commit()

        flash('Deleted dance {} because no song is related any more.'.format(old_dance.name))


def get_or_add_artist_and_dance(form):
    """
    Get the artist and the dance with the names form the form from the db.
    If they are not present, create new ones.
    """
    dance, dance_created_new = Dance.get_or_add_dance(form.dance_name.data)

    if dance_created_new:
        flash("No dance with the name {dance_name}. Created a new one.".format(dance_name=dance.name))

    artist, artist_created_new = Artist.get_or_add_artist(form.artist_name.data)

    if artist_created_new:
        flash("No artist with the name {artist_name}. Created a new one.".format(artist_name=artist.name))

    return artist, dance


def get_song_duration(file_name_with_this_dance):
    audio_file = MP3(file_name_with_this_dance)
    return timedelta(seconds=audio_file.info.length)


def create_file_path(form):
    file_name = SONG_PATH_FORMAT.format(dance_name=form.dance_name.data,
                                        artist_name=form.artist_name.data,
                                        title=form.title.data)
    upload_path = os.path.join(app.root_path, app.config["DATA_FOLDER"])
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
    form.rating.data = song.get_user_rating(g.user)
    form.path.data = song.path
    form.bpm.data = song.bpm
    user_comment = song.get_user_comment(g.user)
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

        uploaded_file.save(file_path_to_save_to)
        song.duration = get_song_duration(file_path_to_save_to)
        song.path = file_name

        db.session.merge(song)
        db.session.commit()


def change_or_add_song(form, song=None, old_artist=None, old_dance=None):
    artist, dance = get_or_add_artist_and_dance(form)

    if song is None:
        song = Song(creation_user=g.user)
        song_is_new = True
    else:
        song_is_new = False

    song.artist_id = artist.id
    song.dance_id = dance.id
    song.title = form.title.data
    song.bpm = form.bpm.data

    if song_is_new:
        db.session.merge(song)
    else:
        db.session.add(song)

    db.session.commit()

    if hasattr(form, "note"):
        Comment.set_or_add_comment(song, g.user, form.note.data)

    if hasattr(form, "rating"):
        Rating.set_add_or_delete_rating(song, g.user, form.rating.data)

    upload_file_to_song(form, song)

    if old_artist is not None and old_dance is not None:
        if artist != old_artist or dance != old_dance:
            delete_unused_old_entities(old_artist, old_dance)