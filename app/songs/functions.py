from datetime import timedelta

from flask import request, flash, url_for, g
from mutagen.mp3 import MP3

from app import db
from app.functions import render_template_with_user, get_redirect_target, redirect_back_or
from app.songs.models import Song, Dance, Artist, Rating


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