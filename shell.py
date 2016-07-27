#!/usr/bin/env python
import os
import readline
from pprint import pprint

from flask import *
from app import *


def create_db():
    """
    Convenience function to create the db file with all needed tables.
    """
    db.create_all()

print("Type create_db() to create the DB.")
os.environ['PYTHONINSPECT'] = 'True'
