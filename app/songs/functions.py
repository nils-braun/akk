from app import db
from app.songs.models import Song, Dance, Artist, Rating
from app.users.decorators import render_template_with_user
from flask import request, flash, redirect, url_for, g


def delete_entity(FormClass, DataClass, name, song_argument):
    form = FormClass(request.form)
    data_to_delete = []
    if form.validate_on_submit():
        entity = DataClass.query.filter_by(name=form.name.data).first()
        if entity:
            filter_dict={song_argument: entity.id}
            data_to_delete = Song.query.filter_by(**filter_dict).all()

            if form.sure_to_delete.data:

                old_artists_and_dances = [(song.artist, song.dance) for song in data_to_delete]

                db.session.delete(entity)
                db.session.commit()

                for artist, dance in old_artists_and_dances:
                    delete_unused_old_entities(artist, dance)

                flash('Sucessfully deleted %s' % entity.name)
                return redirect(url_for('songs.home'))
            else:
                flash('Are you sure you want to delete?')
                form.sure_to_delete.data = True

        else:
            flash('No %s with this name' % name, 'error-message')
    return render_template_with_user("songs/deletion_form.html", form=form, data_to_delete=data_to_delete, user=g.user)


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
    dance = Dance.query.filter_by(name=form.dance_name.data).first()
    if not dance:
        dance = Dance(name=form.dance_name.data)
        db.session.add(dance)
        db.session.commit()

        flash('No dance with the name {}. Added new.'.format(dance.name))
    artist = Artist.query.filter_by(name=form.artist_name.data).first()
    if not artist:
        artist = Artist(name=form.artist_name.data)
        db.session.add(artist)
        db.session.commit()

        flash('No artist with the name {}. Added new.'.format(artist.name))
    return artist, dance


def set_or_add_rating(song, rating_value):
    query = Rating.query.filter_by(song_id=song.id, user_id=g.user.id)

    if query.count() == 0:
        # Add new rating
        new_rating = Rating(g.user, song)
        new_rating.value = rating_value

        db.session.add(new_rating)
    else:
        # Update old rating
        old_rating = query.one()
        old_rating.value = rating_value
        db.session.merge(old_rating)

    db.session.commit()