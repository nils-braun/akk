from datetime import datetime

from flask import request, render_template, flash, send_from_directory, current_app, session, json
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from werkzeug.utils import unescape

from akk.common.helpers import slugify
from akk.extensions.classy import BaseView, add_methods, redirect_back_or
from akk.common.models import db

from .forms import EditArtistForm, EditDanceForm, CreateSongForm, EditSongForm
from .functions import set_form_from_song, change_or_add_song
from .models import Artist, Dance, Song, Rating, Label, LabelsToSongs
from akk.songs.model_functions import get_comments_except_user, delete_unused_old_entities, delete_unused_only_labels
from .constants import SONG_FILE_FORMAT_WITH_BPM, SONG_FILE_FORMAT_WITHOUT_BPM


class BaseSongHandlerView(BaseView):
    decorators = [login_required]

    def _edit_entity(self, FormClass, DataClass, name, song_argument):
        form = FormClass(request.values)

        data_to_delete = []
        if form.validate_on_submit():
            entity = DataClass.query.filter_by(name=form.name.data).first()
            if entity:
                if form.sure_to_delete.data or form.unsure_to_delete.data:
                    filter_dict = {song_argument: entity.id}
                    data_to_delete = Song.query.filter_by(**filter_dict).all()

                    if form.sure_to_delete.data:
                        old_artists_and_dances = [(song.artist, song.dance) for song in data_to_delete]

                        db.session.delete(entity)
                        db.session.commit()

                        for artist, dance in old_artists_and_dances:
                            delete_unused_old_entities(artist, dance)

                        flash(u'Successfully deleted {}'.format(entity.name))
                        return redirect_back_or(self.__class__.__name__ + ':home')

                    else:
                        flash('Are you sure you want to delete?')
                        form.sure_to_delete.data = True

                elif form.rename.data:
                    new_name = form.rename_name.data
                    if new_name:
                        entity.name = new_name

                        db.session.merge(entity)
                        db.session.commit()

                        return redirect_back_or(self.__class__.__name__ + ':home')
                    else:
                        flash("You have to provide a new name to rename")
            else:
                flash(u'No %s with this name {}'.format(name), 'error-message')
        return render_template("songs/entity_edit_form.html", form=form, data_to_delete=data_to_delete, next=self.next_url)

    def home(self):
        """
        The home screen with the queried songlist.
        """
        query = request.args.get("query", default="")
        sort_by = request.args.get("sort_by", default="")
        favourites = request.args.get("favourites", default="False") == "True"

        return render_template("songs/songlist_home.html", query=query, sort_by=sort_by,
                               favourites=favourites)

    @add_methods(["GET", "POST"])
    def edit_artist(self):
        """
        Delete artist form
        """
        return self._edit_entity(EditArtistForm, Artist, "artist", "artist_id")

    @add_methods(["GET", "POST"])
    def edit_dance(self):
        """
        Delete dance form
        """
        return self._edit_entity(EditDanceForm, Dance, "dance", "dance_id")

    @add_methods(["GET", "POST"])
    def create_song(self):
        """
        Create new song form
        """
        form = CreateSongForm(request.form)

        if form.validate_on_submit():
            change_or_add_song(form)

            flash('Successfully added song')
            return redirect_back_or(self.__class__.__name__ + ':home')

        return render_template("songs/create_song.html", form=form, next=self.next_url)

    @add_methods(["GET", "POST"])
    def edit_song(self):
        """
        Edit or delete a song
        """
        form = EditSongForm(request.form)

        if form.is_submitted():
            # this will be called on reloading the form
            song_id = form.song_id.data
            song = Song.query.filter_by(id=song_id).first()

            if form.edit_button.data and form.validate():
                change_or_add_song(form, song)

                flash('Successfully updated song')
                return redirect_back_or(self.__class__.__name__ + ':home')

            elif form.delete_button.data:
                old_artist = song.artist
                old_dance = song.dance
                old_labels = song.labels

                db.session.delete(song)
                db.session.commit()

                delete_unused_old_entities(old_artist, old_dance)
                delete_unused_only_labels(old_labels)

                flash('Successfully deleted song')

                return redirect_back_or(self.__class__.__name__ + ':home')

        else:
            song_id = request.args.get("song_id")
            song = set_form_from_song(song_id, form)

            if not song:
                return render_template("404.html"), 404

        other_comments = get_comments_except_user(song, current_user)

        last_user_msg = ""
        if song.last_edit_user and song.last_edit_user != current_user:
            last_user_msg = "This song was last opened by {user} on {editing_time}."
            last_user_msg = last_user_msg.format(user=song.last_edit_user.name,
                                                 editing_time=song.last_edit_date.strftime("%d.%m.%Y %H:%M"))

        song.last_edit_user = current_user
        song.last_edit_date = datetime.now()

        db.session.merge(song)
        db.session.commit()

        return render_template("songs/edit_song.html", form=form, other_comments=other_comments,
                               next=self.next_url, last_user_msg=last_user_msg)

    @staticmethod
    def _filter_condition_for_wishlist():
        return Song.is_on_wishlist.is_(False)

    def search(self):
        """
        This page is called by AJAX (javascript) on the home page, to get the
        songlist.

        Arguments to the call are the query, the page and the page_size (defaults to 50).
        """
        page_size = request.args.get("page_size", default=100, type=int)
        page = request.args.get("page", default=0, type=int)
        query_string = unescape(request.args.get("query", default=""))
        sort_by = request.args.get("sort_by", default="")
        favourites = request.args.get("favourites", default="False") == "True"

        average_rating_for_songs = db.session.query(Rating.song_id, func.avg(Rating.value).label("rating")) \
            .group_by(Rating.song_id).subquery()
        user_rating_for_songs = Song.query.join(Rating).with_entities(Rating.song_id, Rating.value.label("rating")) \
            .filter(Rating.user_id == current_user.id) \
            .subquery()

        filter_condition = (Artist.name.contains(query_string) |
                            Dance.name.contains(query_string) |
                            Song.title.contains(query_string) |
                            Label.name.contains(query_string))

        filter_condition &= self._filter_condition_for_wishlist()

        if favourites:
            rating = user_rating_for_songs
        else:
            rating = average_rating_for_songs

        songs_with_queried_content = Song.query.join(Artist, Dance).outerjoin(LabelsToSongs, Label) \
            .filter(filter_condition)
        songs_with_rating = songs_with_queried_content \
            .outerjoin(rating, Song.id == rating.c.song_id) \
            .group_by(Song.id) \
            .with_entities(Song, rating.c.rating.label("rating"))

        ordering_tuples = ()

        if sort_by == "title":
            ordering_tuples += (Song.title,)
        elif sort_by == "artist":
            ordering_tuples += (Artist.name,)
        elif sort_by == "dance":
            ordering_tuples += (Dance.name,)
        elif sort_by == "label":
            ordering_tuples += (Label.name,)
        elif sort_by == "rating":
            ordering_tuples += (desc("rating"),)
        elif sort_by == "duration":
            ordering_tuples += (desc(Song.duration),)
        elif sort_by == "bpm":
            ordering_tuples += (Song.bpm,)

        ordering_tuples = ordering_tuples + (desc("rating"), Song.title, Dance.name)

        sorted_songs_with_rating = songs_with_rating.order_by(*ordering_tuples)

        songs = sorted_songs_with_rating.limit(page_size).offset(page * page_size).all()

        songs = [(song, get_rating(rating))
                 for song, rating in songs]

        return render_template("songs/search_ajax.html", songs=songs)

    def completion(self):
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
        elif source_column == "label":
            result = [label.name for label in Label.query.filter(Label.name.contains(term)).limit(10).all()]
        elif source_column == "all":
            # TODO: Make faster, see issue #3
            result = [dance.name for dance in Dance.query.filter(Dance.name.contains(term)).limit(10).all()]
            result += [artist.name for artist in Artist.query.filter(Artist.name.contains(term)).limit(10).all()]
            result += [song.title for song in Song.query.filter(Song.title.contains(term)).limit(10).all()]
            result += [label.name for label in Label.query.filter(Label.name.contains(term)).limit(10).all()]
        else:
            return render_template("404.html"), 404
        return json.dumps([{"label": label} for label in set(result)])


class SongsView(BaseSongHandlerView):
    def reset_download_id(self):
        """
        This page resets the download ID. One link at the home points to that, which will
        immediately redirect back.
        """
        session["download_id"] = 0
        return redirect_back_or(self.__class__.__name__ + ':home')

    def download_song(self):
        """
        This page is called by the download button (created with javascript), when a song should be downloaded.

        Arguments are the song_id of the song to download. The path and the download filename will be
        automatically deducted.
        """
        song_id = request.args["song_id"]

        song = Song.query.filter_by(id=song_id).first()

        if not song:
            return render_template("404.html"), 404
        else:
            if "download_id" not in session:
                session["download_id"] = 0

            # TODO: include MP3 tags

            if song.bpm:
                attachment_filename = SONG_FILE_FORMAT_WITH_BPM.format(id=session["download_id"], song=song)
            else:
                attachment_filename = SONG_FILE_FORMAT_WITHOUT_BPM.format(id=session["download_id"], song=song)

            session["download_id"] += 1

            return send_from_directory(current_app.config["DATA_FOLDER"], song.path, as_attachment=True,
                                       attachment_filename=slugify(attachment_filename))

    def serve_song(self):
        """
        This page is called by the audio HTML element (created with javascript), when a song should be played.

        Arguments are the song_id of the song to play. The path will be automatically deducted.
        """
        song_id = request.args["song_id"]

        song = Song.query.filter_by(id=song_id).first()

        if song:
            return send_from_directory(current_app.config["DATA_FOLDER"], song.path, as_attachment=False)
        else:
            return render_template("404.html"), 404



class WishlistView(BaseSongHandlerView):
    def home(self):
        """
        The home screen with the queried songlist.
        """
        query = request.args.get("query", default="")
        sort_by = request.args.get("sort_by", default="")
        favourites = request.args.get("favourites", default="False") == "True"

        return render_template("songs/wishlist_home.html", query=query, sort_by=sort_by, favourites=favourites)

    @staticmethod
    def _filter_condition_for_wishlist():
        return Song.is_on_wishlist.is_(True)