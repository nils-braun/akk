from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm
from app.songs.functions import delete_entity, delete_unused_old_entities, get_or_add_artist_and_dance, \
    set_or_add_rating
from app.songs.models import Artist, Dance, Song
from app.users.decorators import requires_login
from app.users.models import User
from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for

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


@mod.route('/create_song/', methods=['GET', 'POST'])
@requires_login
def create_song():
    """
    Create new song form
    """
    form = CreateSongForm(request.form)
    if form.validate_on_submit():
        artist, dance = get_or_add_artist_and_dance(form)

        song = Song(title=form.title.data, dance=dance, artist=artist, creation_user=g.user)
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

    if form.is_submitted():
        # this will be called on reloading the form
        song_id = form.song_id.data
        song = Song.query.filter_by(id=song_id).first()

        old_artist = song.artist
        old_dance = song.dance

        if form.validate():
            if form.edit_button.data:

                artist, dance = get_or_add_artist_and_dance(form)

                song.artist_id = artist.id
                song.dance_id = dance.id
                song.title = form.title.data

                db.session.merge(song)
                db.session.commit()

                set_or_add_rating(song, form.rating.data)

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
        form.rating.data = song.get_user_rating(g.user)

    return render_template("songs/edit_song.html", form=form)


