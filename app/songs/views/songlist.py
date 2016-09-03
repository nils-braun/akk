import json

from flask import request
from sqlalchemy import func, desc

from app import db
from app.functions import requires_login, render_template_with_user
from app.songs.models import Rating, Song, Artist, Dance


def add_songlist_views(mod):
    @mod.route('/home/', methods=['GET'])
    @requires_login
    def home():
        """
        The home screen with the queried songlist.
        """
        query = request.args.get("query", default="")
        return render_template_with_user("songs/home.html", query=query)

    @mod.route('/search/', methods=['GET'])
    @requires_login
    def search():
        """
        This page is called by AJAX (javascript) on the home page, to get the
        songlist.

        Arguments to the call are the query, the page and the page_size (defaults to 50).
        """
        page_size = request.args.get("page_size", default=100, type=int)
        page = request.args.get("page", default=0, type=int)
        query_string = request.args.get("query")

        average_rating_for_songs = db.session.query(Rating.song_id, func.avg(Rating.value).label("rating")) \
            .group_by(Rating.song_id).subquery()
        user_rating_for_songs = Song.query.join(Rating).with_entities(Rating.song_id, Rating.value.label("user_rating")) \
            .subquery()

        filter_condition = (Artist.name.contains(query_string) |
                            Dance.name.contains(query_string) |
                            Song.title.contains(query_string))

        songs_with_queried_content = Song.query.join(Artist, Dance).filter(filter_condition)
        songs_with_rating = songs_with_queried_content \
            .outerjoin(average_rating_for_songs, Song.id == average_rating_for_songs.c.song_id) \
            .outerjoin(user_rating_for_songs, Song.id == user_rating_for_songs.c.song_id) \
            .group_by(Song.id) \
            .with_entities(Song, average_rating_for_songs.c.rating.label("rating"),
                           user_rating_for_songs.c.user_rating.label("user_rating")) \
            .order_by(desc("rating"), desc("user_rating"), Dance.name, Song.title)

        songs = songs_with_rating.limit(page_size).offset(page * page_size).all()

        songs = [(song, Song.get_rating(rating), Song.get_rating(user_rating))
                 for song, rating, user_rating in songs]

        return render_template_with_user("songs/search_ajax.html", songs=songs)

    @mod.route("/completion/", methods=['GET'])
    @requires_login
    def completion():
        """
        This page is called by AJAX (javascript) on every custom completion element, to get the list of
        possible entries.
        Arguments are the source (artist or dance or all) and the term (the piece of text, the user has already
        entered).
        """
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