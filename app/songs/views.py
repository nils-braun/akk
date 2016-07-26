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
        artist = Artist.query.filter_by(name=form.name).first()
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
        dance = Dance.query.filter_by(name=form.name).first()
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

        song = Song(title=form.title, dance=dance, artist=artist)
        db.session.add(song)
        db.session.commit()

        flash('Sucessfully added song')
        return redirect(url_for('songs.home'))

    return render_template("songs/create_song.html", form=form)


@mod.route('/edit_song/', methods=['GET', 'POST'])
def register():
    """
    Create new song form
    """
    form = EditSongForm(request.form, g.song)
    if form.validate_on_submit():
        if form.edit_button.data:
            artist, dance = get_or_add_artist_and_dance(form)

            g.song.artist_id = artist.id
            g.song.dance_id = dance.id
            g.song.title = form.title

            db.session.update(g.song)
            db.session.commit()

            flash('Sucessfully updated song')
        elif form.delete_button.data:
            db.session.delete(g.song)
            db.session.commit()

            flash('Sucessfully deleted song')

        return redirect(url_for('songs.home'))

    return render_template("songs/edit_song.html", form=form)


def get_or_add_artist_and_dance(form):
    dance = Dance.query.filter_by(name=form.dance_name).first()
    if not dance:
        flash('No dance with this name. Added new.')

        dance = Dance(name=form.dance_name)
        db.session.add(dance)
        db.session.commit()
    artist = Artist.query.filter_by(name=form.artist_name).first()
    if not artist:
        flash('No dance with this name. Added new.')

        artist = Artist(name=form.artist_name)
        db.session.add(artist)
        db.session.commit()
    return artist, dance
