from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_user, logout_user, login_required
from werkzeug import check_password_hash, generate_password_hash

from akk.common.models import db
from akk.common.helpers import redirect_back_or, get_redirect_target

from .forms import RegisterForm, LoginForm
from .models import User

mod = Blueprint('users', __name__, url_prefix='/users')


@mod.route('/logout/', methods=['GET', 'POST'])
def logout():
    """
    Logout form
    """
    # TODO
    # if "download_id" in session:
    #     session.pop('download_id', None)

    logout_user()
    flash("Successfully logged out.")

    return redirect(url_for("users.login"))


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    form = LoginForm(request.form)
    next_url = get_redirect_target()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # we use werzeug to validate user's password
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(u'Welcome {}'.format(user.name))

            return redirect_back_or('songs.home')

        flash('Wrong email or password', 'error-message')
    return render_template("users/login.html", form=form, next=next_url)


@mod.route('/register/', methods=['GET', 'POST'])
@login_required
def register():
    """
    Registration Form
    """
    form = RegisterForm(request.form)
    next_url = get_redirect_target()

    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, password=generate_password_hash(form.password.data))

        db.session.add(user)
        db.session.commit()

        flash('Thanks for registering')
        return redirect_back_or('songs.home')
    return render_template("users/register.html", form=form, next=next_url)