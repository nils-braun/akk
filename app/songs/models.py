from datetime import datetime

from sqlalchemy import not_

from app import db
import app.songs.constants as SONGS
from app.users.models import User


class Dance(db.Model):
    """
    Class representing a dance type.
    """
    __tablename__ = 'songs_dances'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)

    @staticmethod
    def get_or_add_dance(dance_name):
        dance = Dance.query.filter_by(name=dance_name).first()
        dance_created_new = False
        if not dance:
            dance = Dance(name=dance_name)
            db.session.add(dance)
            db.session.commit()

            dance_created_new = True

        return dance, dance_created_new

    def __init__(self, name):
        """
        Create a new dance.
        """
        self.name = name

    def __repr__(self):
        return "Dance: {self.name} ({self.id})".format(self=self)


class Artist(db.Model):
    """
    Class representing an artist.
    """
    __tablename__ = 'songs_artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)

    @staticmethod
    def get_or_add_artist(artist_name):
        artist = Artist.query.filter_by(name=artist_name).first()
        artist_created_new = False
        if not artist:
            artist = Artist(name=artist_name)
            db.session.add(artist)
            db.session.commit()

            artist_created_new = True

        return artist, artist_created_new

    def __init__(self, name):
        """
        Create a new artist.
        """
        self.name = name

    def __repr__(self):
        return "Artist: {self.name} ({self.id})".format(self=self)


class Song(db.Model):
    """
    Class representing a song.
    """
    __tablename__ = "songs_songs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(350), nullable=False)
    path = db.Column(db.Unicode(500), nullable=False, default="")

    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.__tablename__ + '.id'))
    # Delete when artists is deleted
    artist = db.relationship(Artist, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    dance_id = db.Column(db.Integer, db.ForeignKey(Dance.__tablename__ + '.id'))
    # Delete when dance is deleted
    dance = db.relationship(Dance, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    creation_user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    # Delete when user is deleted
    creation_user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))

    def get_user_rating(self, user):
        query = Rating.query.filter_by(song_id=self.id, user_id=user.id)
        if query.count() > 0:
            return query.one().value
        else:
            return SONGS.NOT_RATED_STRING

    @staticmethod
    def get_rating_as_string(rating):
        if rating is not None:
            return "%.1f" % rating
        else:
            return SONGS.NOT_RATED_STRING

    def get_comments_except_user(self, user):
        return Comment.query.filter(Comment.song_id==self.id, not_(Comment.user_id==user.id)).all()

    def get_user_comment(self, user):
        query = Comment.query.filter_by(song_id=self.id, user_id=user.id)
        if query.count() > 0:
            return query.one()
        else:
            return None

    def get_number_of_playlists(self):
        # TODO
        return 0

    def __init__(self, title, artist, dance, creation_user):
        """
        Create a new song.
        """
        self.title = title
        self.artist_id = artist.id
        self.dance_id = dance.id
        self.creation_user_id = creation_user.id

    def __repr__(self):
        return "Song: {self.title} ({self.id}) - {self.artist} - {self.dance}".format(self=self)


class Rating(db.Model):
    __tablename__ = "songs_ratings"
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    # Delete when user is deleted
    user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"))
    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    no_double_rating_constraint = db.UniqueConstraint(user_id, song_id)

    def __init__(self, user, song):
        self.song_id = song.id
        self.user_id = user.id

    @staticmethod
    def set_or_add_rating(song, user, rating_value):
        query = Rating.query.filter_by(song_id=song.id, user_id=user.id)

        if query.count() == 0:
            # Add new rating
            new_rating = Rating(g.user, song)
            new_rating.value = rating_value

            db.session.add(new_rating)
        else:
            # Update old rating
            old_rating = query.one()
            old_rating.value = rating_value
            db.session.merge(old_rating)

        db.session.commit()


class Comment(db.Model):
    __tablename__ = "songs_comments"
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Unicode(1000), nullable=False)
    creation_date = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + ".id"))
    # Delete when user is deleted
    user = db.relationship(User, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"))
    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade='delete,all'))
    no_double_comment_constraint = db.UniqueConstraint(user_id, song_id)

    def __init__(self, user, song):
        self.song_id = song.id
        self.user_id = user.id
        self.creation_date = datetime.now()

    @staticmethod
    def set_or_add_comment(song, user, note_value):
        query = Comment.query.filter_by(song_id=song.id, user_id=user.id)

        if query.count() == 0:
            # Add new rating
            new_comment = Comment(user, song)
            new_comment.note = note_value

            db.session.add(new_comment)
        else:
            # Update old rating
            old_comment = query.one()
            old_comment.note = note_value
            db.session.merge(old_comment)

        db.session.commit()
