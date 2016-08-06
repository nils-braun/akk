import json

from sqlalchemy import desc
from sqlalchemy import func

from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm, SearchSongForm
from app.songs.functions import delete_entity, delete_unused_old_entities, get_or_add_artist_and_dance, \
    set_or_add_rating
from app.songs.models import Artist, Dance, Song, Rating
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


@mod.route('/home/', methods=['GET'])
@requires_login
def home():
    if "query" in request.args:
        query = request.args["query"]
    else:
        query = ""

    return render_template_with_user("songs/home.html", query=query)


@mod.route('/search/', methods=['GET'])
@requires_login
def search():
    if "page_size" in request.args:
        page_size = int(request.args["page_size"])
    else:
        page_size = 100

    if "page" in request.args:
        page = int(request.args["page"])
    else:
        page = 0

    query_string = request.args["query"]

    average_rating_for_songs = db.session.query(Rating.song_id, func.avg(Rating.value).label("rating"))\
        .group_by(Rating.song_id).subquery()
    user_rating_for_songs = Song.query.join(Rating).with_entities(Rating.song_id, Rating.value.label("user_rating"))\
        .subquery()

    filter_condition = (Artist.name.contains(query_string) |
                        Dance.name.contains(query_string) |
                        Song.title.contains(query_string))

    songs_with_queried_content = Song.query.join(Artist, Dance).filter(filter_condition)
    songs_with_rating = songs_with_queried_content\
        .outerjoin(average_rating_for_songs, Song.id==average_rating_for_songs.c.song_id)\
        .outerjoin(user_rating_for_songs, Song.id == user_rating_for_songs.c.song_id)\
        .with_entities(Song, average_rating_for_songs.c.rating.label("rating"), user_rating_for_songs.c.user_rating.label("user_rating"))\
        .order_by(desc("rating"), desc("user_rating"), Dance.name, Song.title)

    songs = songs_with_rating.limit(page_size).offset(page*page_size).all()

    songs = [(song, Song.get_rating_as_string(rating), Song.get_rating_as_string(user_rating))
             for song, rating, user_rating in songs]

    return render_template_with_user("songs/search_ajax.html", songs=songs)


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
        # TODO: Make faster
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
