# Some general utility functions used throughout the project.
from flask import redirect, url_for, render_template


def set_basic_configuration_and_views(app):
    """
    Set the configurations and functionality specific to this project:
        1. Add a proper error page
        2. Add the user functionality and views
        3. Add the songs functionality and views
        4. Set the start page to be songs/home

    :param app: Which app to configure
    """
    if not app.config['DEBUG']:
        from akk.common.helpers import install_secret_key
        install_secret_key(app)

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    from akk.users.views import mod as users_module
    app.register_blueprint(users_module)

    from akk.songs.views import mod as songs_module
    app.register_blueprint(songs_module)

    @app.route("/")
    def index():
        return redirect(url_for("songs.home"))

