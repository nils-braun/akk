from flask import request, send_from_directory, session

from app import app
from app.functions import requires_login, render_template_with_user, redirect_back_or
from app.songs.constants import SONG_FILE_FORMAT
from app.songs.models import Song


def add_playlist_views(mod):
    @mod.route("/serve/", methods=['GET'])
    @requires_login
    def serve_song():
        """
        This page is called by the audio HTML element (created with javascript), when a song should be played.

        Arguments are the song_id of the song to play. The path will be automatically deducted.
        """
        song_id = request.args["song_id"]

        song = Song.query.filter_by(id=song_id).first()

        if song:
            return send_from_directory(app.config["DATA_FOLDER"], song.path, as_attachment=False)
        else:
            return render_template_with_user("404.html"), 404

    @mod.route("/download/", methods=['GET'])
    @requires_login
    def download_song():
        """
        This page is called by the download button (created with javascript), when a song should be downloaded.

        Arguments are the song_id of the song to download. The path and the download filename will be
        automatically deducted.
        """
        song_id = request.args["song_id"]

        song = Song.query.filter_by(id=song_id).first()

        if not song:
            return render_template_with_user("404.html"), 404
        else:
            if "download_id" not in session:
                session["download_id"] = 0

            attachment_filename = ("{id} - " + SONG_FILE_FORMAT).format(
                id=session["download_id"], title=song.title, artist_name=song.artist.name, dance_name=song.dance.name)

            session["download_id"] += 1

            return send_from_directory(app.config["DATA_FOLDER"], song.path, as_attachment=True,
                                       attachment_filename=attachment_filename)

    @mod.route("/reset_download_id/")
    @requires_login
    def reset_download_id():
        """
        This page resets the download ID. One link at the home points to that, which will
        immediately redirect back.
        """
        session["download_id"] = 0
        return redirect_back_or("songs.home")