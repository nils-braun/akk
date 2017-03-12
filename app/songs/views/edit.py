from flask import request, g, flash

from app import db
from app.functions import requires_login, get_redirect_target, redirect_back_or, render_template_with_user
from app.songs.forms import EditArtistForm, EditDanceForm, CreateSongForm, EditSongForm
from app.songs.functions import edit_entity, delete_unused_old_entities, set_form_from_song, change_or_add_song, \
    delete_unused_only_labels, set_as_editing, unset_as_editing
from app.songs.models import Artist, Dance, Song


def add_song_edit_views(mod):
    @mod.route('/edit_artist/', methods=['GET', 'POST'])
    @requires_login
    def edit_artist():
        """
        Delete artist form
        """
        return edit_entity(EditArtistForm, Artist, "artist", "artist_id")

    @mod.route('/edit_dance/', methods=['GET', 'POST'])
    @requires_login
    def edit_dance():
        """
        Delete dance form
        """
        return edit_entity(EditDanceForm, Dance, "dance", "dance_id")

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

            if form.edit_button.data and form.validate():
                change_or_add_song(form, song)

                unset_as_editing(song)

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

        else:
            song_id = request.args.get("song_id")
            song = set_form_from_song(song_id, form)

            if not song:
                return render_template_with_user("404.html"), 404

        other_comments = song.get_comments_except_user(g.user)

        last_user_msg = ""
        if song.last_edit_user and song.last_edit_user != g.user:
            last_user_msg = "This song was last opened by {user} on {editing_time}."
            last_user_msg = last_user_msg.format(user=song.last_edit_user.name, editing_time=song.last_edit_date.strftime("%d.%m.%Y %H:%M"))

        set_as_editing(song)

        return render_template_with_user("songs/edit_song.html", form=form, other_comments=other_comments,
                                         next=next_url, last_user_msg=last_user_msg)
