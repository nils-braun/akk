from datetime import timedelta

from akk.common.models import db
from akk.users.models import User


class Dance(db.Model):
    """
    Class representing a dance type.
    """
    __tablename__ = 'songs_dances'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)


class Artist(db.Model):
    """
    Class representing an artist.
    """
    __tablename__ = 'songs_artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)


class Label(db.Model):
    __tablename__ = "songs_labels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(150), unique=True)
    color = db.Column(db.Unicode(6))


class Song(db.Model):
    """
    Class representing a song.
    """
    __tablename__ = "songs_songs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(350), nullable=False)
    path = db.Column(db.Unicode(500), nullable=False, default="")
    duration = db.Column(db.Interval, nullable=False, default=timedelta())
    bpm = db.Column(db.Integer, nullable=False, default=0)
    last_edit_date = db.Column(db.DateTime, nullable=True, default=None)
    is_on_wishlist = db.Column(db.Boolean, nullable=False, default=False)

    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.__tablename__ + '.id'))
    dance_id = db.Column(db.Integer, db.ForeignKey(Dance.__tablename__ + '.id'))
    creation_user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    last_edit_user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"), nullable=True, default=None)

    # Delete when artists is deleted
    artist = db.relationship(Artist, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    # Delete when dance is deleted
    dance = db.relationship(Dance, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    # Delete when user is deleted
    creation_user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'),
                                    foreign_keys=[creation_user_id])
    # Delete when user is deleted
    last_edit_user = db.relationship(User, backref=db.backref("currently_editing_songs", uselist=True, cascade='delete,all'),
                                     foreign_keys=[last_edit_user_id])

    labels = db.relationship(Label, secondary="songs_labels_to_songs")

    no_double_naming = db.UniqueConstraint(artist_id, dance_id, title)


class Rating(db.Model):
    __tablename__ = "songs_ratings"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"))

    # Delete when user is deleted
    user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))

    no_double_rating_constraint = db.UniqueConstraint(user_id, song_id)


class Comment(db.Model):
    __tablename__ = "songs_comments"
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Unicode(1000), nullable=False)
    creation_date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"))

    # Delete when user is deleted
    user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))

    no_double_comment_constraint = db.UniqueConstraint(user_id, song_id)


class LabelsToSongs(db.Model):
    __tablename__ = "songs_labels_to_songs"
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"), primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.__tablename__ + ".id"), primary_key=True)

    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade="delete,all"))
    # Delete when label is deleted
    label = db.relationship(Label, backref=db.backref(__tablename__, uselist=True, cascade="delete,all"))
