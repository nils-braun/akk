# Main entry point for the web service. Here we will create a new "app" instance,
# which is the Flask web service, and add all the needed configuration options
# for this project.
from flask import Flask


def create_app(config_filename):
    # Create a new Flask application
    app = Flask(__name__)

    # Load some configuration options from the file config.py
    app.config.from_pyfile(config_filename)

    # Create a new database connection, we will use everywhere, using the settings in this application
    from akk.common.models import db
    db.init_app(app)

    # Add the configurations and functionality specific to this web service.
    from akk.functions import set_basic_configuration_and_views
    set_basic_configuration_and_views(app)

    return app
