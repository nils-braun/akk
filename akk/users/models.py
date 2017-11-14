from flask_login import UserMixin

from akk.common.models import db


class User(db.Model, UserMixin):
    """
    Class representing the users.
    """
    __tablename__ = 'users_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), unique=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))

    def __init__(self, name=None, email=None, password=None):
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self):
        return "User: {self.name} ({self.id})".format(self=self)
