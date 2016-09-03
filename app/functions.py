import os
import sys
from functools import wraps
from urllib.parse import urlparse, urljoin

from flask import session, g, flash, redirect, url_for, request, render_template


def add_before_request(mod):
    """
    pull user's profile from the database before every request are treated
    """

    def before_request():
        g.user = None
        if 'user_id' in session:
            from app.users.models import User
            g.user = User.query.get(session['user_id'])

    mod.before_request(before_request)


def requires_login(f):
    """
    Function decorator to add a required logged in user to a flask route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash(u'You need to be signed in for this page.')
            return redirect(url_for('users.login', next=request.path))
        return f(*args, **kwargs)

    return decorated_function


def render_template_with_user(template_path, **kwargs):
    if g.user:
        return render_template(template_path, user=g.user, **kwargs)
    else:
        return render_template(template_path, **kwargs)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back_or(endpoint, **values):
    target = request.form.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def install_secret_key(app, filename='secret_key'):
    """Configure the SECRET_KEY from a file
    in the instance directory.

    If the file does not exist, print instructions
    to create it from a shell with a random key,
    then exit.
    """
    filename = os.path.join(app.instance_path, filename)

    try:
        app.config['SECRET_KEY'] = open(filename, 'rb').read()
    except IOError:
        print('Error: No secret key. Create it with:')
        full_path = os.path.dirname(filename)
        if not os.path.isdir(full_path):
            print('mkdir -p {filename}'.format(filename=full_path))
        print('head -c 24 /dev/urandom > {filename}'.format(filename=filename))
        sys.exit(1)


def set_basic_configuration_and_views(app):
    if not app.config['DEBUG']:
        install_secret_key(app)

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    from app.users.views import mod as users_module
    app.register_blueprint(users_module)

    from app.songs.views import mod as songs_module
    app.register_blueprint(songs_module)

    @app.route("/")
    def index():
        return redirect(url_for("songs.home"))