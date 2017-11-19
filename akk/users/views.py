from flask import request, flash, redirect, render_template, session, url_for
from flask_login import login_user, logout_user, login_required
from werkzeug import check_password_hash, generate_password_hash

from akk.common.models import db
from akk.extensions.classy import add_methods, BaseView, redirect_back_or

from .forms import RegisterForm, LoginForm
from .models import User


class UsersView(BaseView):
    def logout(self):
        """
            Logout form
            """
        if "download_id" in session:
            session.pop('download_id', None)

        logout_user()
        flash("Successfully logged out.")

        return redirect(url_for("UsersView:login"))

    @login_required
    @add_methods(["GET", "POST"])
    def register_user(self):
        """
        Registration Form
        """
        form = RegisterForm(request.form)

        if form.validate_on_submit():
            user = User(name=form.name.data, email=form.email.data, password=generate_password_hash(form.password.data))

            db.session.add(user)
            db.session.commit()

            flash('Thanks for registering')
            return redirect_back_or("SongsView:home")
        return render_template("users/register.html", form=form, next=self.next_url)

    @add_methods(["GET", "POST"])
    def login(self):
        form = LoginForm(request.form)

        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            # we use werkzeug to validate user's password
            if user and check_password_hash(user.password, form.password.data):
                login_user(user, remember=True)
                flash(u'Welcome {}'.format(user.name))

                return redirect_back_or("SongsView:home")

            flash('Wrong email or password', 'error-message')
        return render_template("users/login.html", form=form, next=self.next_url)