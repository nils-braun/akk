from flask import Blueprint

from app.functions import add_before_request
from app.songs.views.edit import add_song_edit_views
from app.songs.views.playlist import add_playlist_views
from app.songs.views.songlist import add_songlist_views

mod = Blueprint('songs', __name__, url_prefix='/songs')

add_before_request(mod)
add_songlist_views(mod)
add_playlist_views(mod)
add_song_edit_views(mod)