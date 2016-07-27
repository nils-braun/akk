from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for

from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm
from app.songs.models import Artist, Dance, Song
from app.users.models import User
from app.users.decorators import requires_login

mod = Blueprint('songs', __name__, url_prefix='/songs')


@mod.route('/home/')
@requires_login
def home():
    songs = Song.query.all()
    return render_template("songs/list.html", user=g.user, songs=songs)


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@mod.route('/delete_artist/', methods=['GET', 'POST'])
@requires_login
def delete_artist():
    """
    Delete artist form
    """
    return delete_entity(DeleteArtistForm, Artist, "artist", "artist_id")


@mod.route('/delete_dance/', methods=['GET', 'POST'])
@requires_login
def delete_dance():
    """
    Delete dance form
    """
    return delete_entity(DeleteDanceForm, Dance, "dance", "dance_id")


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
    return render_template("songs/deletion_form.html", form=form, data_to_delete=data_to_delete)


@mod.route('/create_song/', methods=['GET', 'POST'])
@requires_login
def create_song():
    """
    Create new song form
    """
    form = CreateSongForm(request.form)
    if form.validate_on_submit():
        artist, dance = get_or_add_artist_and_dance(form)

        song = Song(title=form.title.data, dance=dance, artist=artist)
        db.session.add(song)
        db.session.commit()

        flash('Sucessfully added song')
        return redirect(url_for('songs.home'))

    return render_template("songs/create_song.html", form=form)


@mod.route('/edit_song/', methods=['GET', 'POST'])
@requires_login
def edit_song():
    """
    Edit or delete a song
    """
    form = EditSongForm(request.form)

    if form.validate_on_submit():
        # this will be called on reloading the form
        song_id = form.song_id.data
        song = Song.query.filter_by(id=song_id).first()

        old_artist = song.artist
        old_dance = song.dance

        if form.edit_button.data:

            artist, dance = get_or_add_artist_and_dance(form)

            song.artist_id = artist.id
            song.dance_id = dance.id
            song.title = form.title.data

            db.session.merge(song)
            db.session.commit()

            if artist != old_artist or dance != old_dance:
                delete_unused_old_entities(old_artist, old_dance)

            flash('Sucessfully updated song')
        elif form.delete_button.data:
            db.session.delete(song)
            db.session.commit()

            delete_unused_old_entities(old_artist, old_dance)

            flash('Sucessfully deleted song')

        return redirect(url_for('songs.home'))

    else:
        # it seems we are coming directly from the main page
        song_id = request.args.get("song_id")

        song = Song.query.filter_by(id=song_id).first()

        if not song:
            return render_template("404.html")

        form.song_id.data = song_id
        form.title.data = song.title
        form.artist_name.data = song.artist.name
        form.dance_name.data = song.dance.name

    return render_template("songs/edit_song.html", form=form)


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
