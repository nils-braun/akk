from flask import request, g, flash

from app import db
from app.functions import requires_login, get_redirect_target, redirect_back_or, render_template_with_user
from app.songs.forms import DeleteArtistForm, DeleteDanceForm, CreateSongForm, EditSongForm
from app.songs.functions import delete_entity, delete_unused_old_entities, set_form_from_song, change_or_add_song, \
    delete_unused_only_labels
from app.songs.models import Artist, Dance, Song


def add_song_edit_views(mod):
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
            change_or_add_song(form)

            flash('Sucessfully added song')
            return redirect_back_or('songs.home')

        return render_template_with_user("songs/create_song.html", form=form, next=next_url)

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

            if form.edit_button.data and form.validate():
                change_or_add_song(form, song)

                flash('Sucessfully updated song')

                return redirect_back_or('songs.home')

            elif form.delete_button.data:
                old_artist = song.artist
                old_dance = song.dance
                old_labels = song.labels

                db.session.delete(song)
                db.session.commit()

                delete_unused_old_entities(old_artist, old_dance)
                delete_unused_only_labels(old_labels)

                flash('Sucessfully deleted song')

                return redirect_back_or('songs.home')

            return render_template_with_user("songs/edit_song.html", form=form, other_comments=other_comments,
                                             next=next_url)
        else:
            song_id = request.args.get("song_id")
            song = set_form_from_song(song_id, form)

            if not song:
                return render_template_with_user("404.html"), 404

            other_comments = song.get_comments_except_user(g.user)

            return render_template_with_user("songs/edit_song.html", form=form, other_comments=other_comments,
                                             next=next_url)
