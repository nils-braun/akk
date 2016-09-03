from flask import Blueprint

from app.functions import add_before_request
from app.songs.views.views import add_song_views

mod = Blueprint('songs', __name__, url_prefix='/songs')
add_before_request(mod)
add_song_views(mod)