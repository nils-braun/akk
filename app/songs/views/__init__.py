from flask import Blueprint, g, session

from app.users.models import User

mod = Blueprint('songs', __name__, url_prefix='/songs')

from app.songs.views.views import *


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])