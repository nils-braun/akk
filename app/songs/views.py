from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for

from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm
from app.songs.models import Artist, Dance, Song
from app.users.models import User
from app.users.decorators import requires_login

mod = Blueprint('songs', __name__, url_prefix='/songs')


@mod.route('/me/')
@requires_login
def home():
    raise NotImplementedError()
    #return render_template("songs/list.html", user=g.user)


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@mod.route('/delete_artist/', methods=['GET', 'POST'])
def delete_artist():
    """
    Delete artist form
    """
    form = DeleteArtistForm(request.form)
    if form.validate_on_submit():
        artist = Artist.query.filter_by(name=form.name.data).first()
        if artist:
            db.session.delete(artist)
            db.session.commit()

            flash('Sucessfully deleted %s' % artist.name)
            return redirect(url_for('songs.home'))

        flash('No artist with this name', 'error-message')
    return render_template("songs/delete_artist.html", form=form)


@mod.route('/delete_dance/', methods=['GET', 'POST'])
def delete_dance():
    """
    Delete dance form
    """
    form = DeleteDanceForm(request.form)
    if form.validate_on_submit():
        dance = Dance.query.filter_by(name=form.name.data).first()
        if dance:
            db.session.delete(dance)
            db.session.commit()

            flash('Sucessfully deleted %s' % dance.name)
            return redirect(url_for('songs.home'))

        flash('No dance with this name', 'error-message')
    return render_template("songs/delete_dance.html", form=form)


@mod.route('/create_song/', methods=['GET', 'POST'])
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
def edit_song():
    """
    Edit or delete a song
    """

    form = EditSongForm(request.form)

    if not form.song_id:
        # it seems we are coming directly from the main page
        song_id = request.args.get("song_id")
        song = Song.query.filter_by(id=song_id).first()

        form.song_id = song.id
        form.artist_name.data = song.artist.name
        form.dance_name.data = song.dance.name

        if not song:
            return render_template("404.html")

    else:
        # this will be called on reloading the form
        song_id = form.song_id
        song = Song.query.filter_by(id=song_id).first()

    if form.validate_on_submit():
        if form.edit_button.data:
            artist, dance = get_or_add_artist_and_dance(form)

            song.artist_id = artist.id
            song.dance_id = dance.id
            song.title = form.title.data

            db.session.update(g.song)
            db.session.commit()

            flash('Sucessfully updated song')
        elif form.delete_button.data:
            db.session.delete(song)
            db.session.commit()

            flash('Sucessfully deleted song')

        return redirect(url_for('songs.home'))

    return render_template("songs/edit_song.html", form=form)


def get_or_add_artist_and_dance(form):
    """
    Get the artist and the dance with the names form the form from the db.
    If they are not present, create new ones.
    """
    dance = Dance.query.filter_by(name=form.dance_name.data).first()
    if not dance:
        flash('No dance with this name. Added new.')

        dance = Dance(name=form.dance_name.data)
        db.session.add(dance)
        db.session.commit()
    artist = Artist.query.filter_by(name=form.artist_name.data).first()
    if not artist:
        flash('No artist with this name. Added new.')

        artist = Artist(name=form.artist_name.data)
        db.session.add(artist)
        db.session.commit()
    return artist, dance
