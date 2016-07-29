from functools import wraps

from flask import g, flash, redirect, url_for, request, render_template


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