#!/usr/bin/env python
import os
import readline
from pprint import pprint

from app.songs.models import Song, Artist, Dance
from app.users.models import User
from flask import *
from app import *


def create_db():
    """
    Convenience function to create the db file with all needed tables.
    """
    db.create_all()

    user = User(u"test", "test@test.com", "pbkdf2:sha1:1000$VUu0UWDW$211afd0957df48d23553a119668dbc331b84c8cd")
    db.session.add(user)
    db.session.commit()


if __name__ == '__main__':
    print("Type create_db() to create the DB.")
    os.environ['PYTHONINSPECT'] = 'True'
