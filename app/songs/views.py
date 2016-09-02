import json

from flask.helpers import send_from_directory
from sqlalchemy import desc
from sqlalchemy import func

from app import db
from app.songs.forms import CreateSongForm, DeleteArtistForm, DeleteDanceForm, EditSongForm
from app.songs.functions import delete_entity, delete_unused_old_entities, get_or_add_artist_and_dance
from app.songs.models import Artist, Dance, Song, Rating, Comment
from app.functions import requires_login, render_template_with_user, get_redirect_target, redirect_back_or
from app.users.models import User
from flask import Blueprint, request, flash, g, session

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
    query = request.args.get("query", default="")
    return render_template_with_user("songs/home.html", query=query)


@mod.route('/search/', methods=['GET'])
@requires_login
def search():
    page_size = request.args.get("page_size", default=100, type=int)
    page = request.args.get("page", default=0, type=int)
    query_string = request.args.get("query")

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
        .group_by(Song.id)\
        .with_entities(Song, average_rating_for_songs.c.rating.label("rating"), user_rating_for_songs.c.user_rating.label("user_rating"))\
        .order_by(desc("rating"), desc("user_rating"), Dance.name, Song.title)

    songs = songs_with_rating.limit(page_size).offset(page*page_size).all()

    songs = [(song, Song.get_rating(rating), Song.get_rating(user_rating))
             for song, rating, user_rating in songs]

    return render_template_with_user("songs/search_ajax.html", songs=songs)


@mod.route("/completion/", methods=['GET'])
@requires_login
def completion():
    source_column = request.args.get("source")
    term = request.args.get("term")

    if source_column == "dance":
        result = [dance.name for dance in Dance.query.filter(Dance.name.contains(term)).limit(10).all()]
    elif source_column == "artist":
        result = [artist.name for artist in Artist.query.filter(Artist.name.contains(term)).limit(10).all()]
    elif source_column == "all":
        # TODO: Make faster, see issue #3
        result = [dance.name for dance in Dance.query.filter(Dance.name.contains(term)).limit(10).all()]
        result += [artist.name for artist in Artist.query.filter(Artist.name.contains(term)).limit(10).all()]
        result += [song.title for song in Song.query.filter(Song.title.contains(term)).limit(10).all()]
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
    next_url = get_redirect_target()

    if form.validate_on_submit():
        artist, dance = get_or_add_artist_and_dance(form)

        song = Song(title=form.title.data, dance=dance, artist=artist, creation_user=g.user)
        db.session.add(song)
        db.session.commit()

        flash('Sucessfully added song')
        return redirect_back_or('songs.home')

    return render_template_with_user("songs/create_song.html", form=form, next=next_url)


@mod.route("/serve/", methods=['GET'])
@requires_login
def serve_song():
    filename = request.args["filename"]
    if filename.startswith("/"):
        filename = filename[1:]
    return send_from_directory("data", filename, as_attachment=False)


@mod.route("/download/", methods=['GET'])
@requires_login
def download_song():
    filename = request.args["filename"]
    if filename.startswith("/"):
        filename = filename[1:]

    attachment_filename = filename

    if "download_id" not in session:
        session["download_id"] = 0

    attachment_filename = "{id} - {filename}".format(id=session["download_id"], filename=attachment_filename)

    session["download_id"] += 1

    return send_from_directory("data", filename, as_attachment=True, attachment_filename=attachment_filename)

@mod.route("/reset_download_id/")
@requires_login
def reset_download_id():
    session["download_id"] = 0
    return redirect_back_or("songs.home")

@mod.route('/edit_song/', methods=['GET', 'POST'])
@requires_login
def edit_song():
    """
    Edit or delete a song
    """
    form = EditSongForm(request.form)
    next_url = get_redirect_target()

    if form.is_submitted():
        # this will be called on reloading the form
        song_id = form.song_id.data
        song = Song.query.filter_by(id=song_id).first()

        other_comments = song.get_comments_except_user(g.user)

        old_artist = song.artist
        old_dance = song.dance

        if form.edit_button.data and form.validate():

            artist, dance = get_or_add_artist_and_dance(form)

            song.artist_id = artist.id
            song.dance_id = dance.id
            song.title = form.title.data
            song.bpm = form.bpm.data

            db.session.merge(song)
            db.session.commit()

            if form.note.data != "":
                Comment.set_or_add_comment(song, g.user, form.note.data)

            if int(form.rating.data) != 0:
                Rating.set_or_add_rating(song, g.user, form.rating.data)
            else:
                rating_query = Rating.query.filter_by(song_id=song.id, user_id=g.user.id)
                if rating_query.count() > 0:
                    for rating_to_delete in rating_query.all():
                        db.session.delete(rating_to_delete)
                    db.session.commit()

            if artist != old_artist or dance != old_dance:
                delete_unused_old_entities(old_artist, old_dance)

            flash('Sucessfully updated song')

            return redirect_back_or('songs.home')
        elif form.delete_button.data:
            db.session.delete(song)
            db.session.commit()

            delete_unused_old_entities(old_artist, old_dance)

            flash('Sucessfully deleted song')

            return redirect_back_or('songs.home')

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
        form.path.data = song.path
        form.bpm.data = song.bpm

        user_comment = song.get_user_comment(g.user)
        if user_comment:
            form.note.data = user_comment.note

        other_comments = song.get_comments_except_user(g.user)

    return render_template_with_user("songs/edit_song.html", form=form, other_comments=other_comments, next=next_url)
