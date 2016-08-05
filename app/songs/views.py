import json

from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm, SearchSongForm
from app.songs.functions import delete_entity, delete_unused_old_entities, get_or_add_artist_and_dance, \
    set_or_add_rating
from app.songs.models import Artist, Dance, Song
from app.users.decorators import requires_login, render_template_with_user
from app.users.models import User
from flask import Blueprint, request, flash, g, session, redirect, url_for

mod = Blueprint('songs', __name__, url_prefix='/songs')


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@mod.route('/home/', methods=['POST', 'GET'])
@requires_login
def home():
    # TODO: Fix performance issues and make dynamic!
    form = SearchSongForm(request.args)
    if form.validate():
        query_string = form.query.data

        songs_with_queried_title = Song.query.filter(Song.title.contains(query_string)).all()
        songs_with_queried_artist = Song.query.join(Artist).filter(Artist.name.contains(query_string)).all()
        songs_with_queried_dance = Song.query.join(Dance).filter(Dance.name.contains(query_string)).all()

        songs = set(songs_with_queried_title + songs_with_queried_artist + songs_with_queried_dance)
    else:
        songs = Song.query.all()

    songs = sorted(songs, key=lambda song: float(song.get_rating_as_number()), reverse=True)
    return render_template_with_user("songs/list.html", songs=songs, form=form)


@mod.route("/completion/", methods=['GET'])
@requires_login
def completion():
    source_column = request.args["source"]
    term = request.args["term"]

    if source_column == "dance":
        result = [dance.name for dance in Dance.query.filter(Dance.name.contains(term)).all()]
    elif source_column == "artist":
        result = [artist.name for artist in Artist.query.filter(Artist.name.contains(term)).all()]
    elif source_column == "all":
        result = [artist.name for artist in Artist.query.filter(Artist.name.contains(term)).all()]
        result += [dance.name for dance in Dance.query.filter(Dance.name.contains(term)).all()]
        result += [song.title for song in Song.query.filter(Song.title.contains(term)).all()]
    else:
        return render_template_with_user("404.html"), 404
    return json.dumps([{"label": label} for label in set(result)])


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

    return render_template_with_user("songs/create_song.html", form=form)


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

        if form.edit_button.data and form.validate():

            artist, dance = get_or_add_artist_and_dance(form)

            song.artist_id = artist.id
            song.dance_id = dance.id
            song.title = form.title.data
            song.note = form.note.data

            db.session.merge(song)
            db.session.commit()

            if form.rating.data != "nr":
                try:
                    int(form.rating.data)
                except:
                    # FIXME: Create a better widget for this.
                    flash("Please insert a numerical rating.", "error-message")
                    return render_template_with_user("songs/edit_song.html", form=form)
                else:
                    set_or_add_rating(song, form.rating.data)

            if artist != old_artist or dance != old_dance:
                delete_unused_old_entities(old_artist, old_dance)

            flash('Sucessfully updated song')

            return redirect(url_for('songs.home'))
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
            return render_template_with_user("404.html"), 404

        form.song_id.data = song_id
        form.title.data = song.title
        form.artist_name.data = song.artist.name
        form.dance_name.data = song.dance.name
        form.rating.data = song.get_user_rating(g.user)
        form.note.data = song.note
        form.path.data = song.path

    return render_template_with_user("songs/edit_song.html", form=form)
