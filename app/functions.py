from functools import wraps
from urllib.parse import urlparse, urljoin

from flask import session, g, flash, redirect, url_for, request, render_template

from app.users.models import User


def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


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