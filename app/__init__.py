from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.functions import set_basic_configuration_and_views

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

set_basic_configuration_and_views(app)