from flask import Blueprint

from .edit import add_song_edit_views
from .playlist import add_playlist_views
from .songlist import add_songlist_views

mod = Blueprint('songs', __name__, url_prefix='/songs')

add_songlist_views(mod)
add_playlist_views(mod)
add_song_edit_views(mod)