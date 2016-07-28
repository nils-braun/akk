from app import db
from app.users.models import User


class Dance(db.Model):
    """
    Class representing a dance type.
    """
    __tablename__ = 'songs_dances'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(250), unique=True, nullable=False)

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
    note = db.Column(db.Unicode(1000), nullable=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('songs_artists.id'))
    # Delete when artists is deleted
    artist = db.relationship(Artist, backref=db.backref("songs_songs", uselist=True, cascade='delete,all'))
    dance_id = db.Column(db.Integer, db.ForeignKey('songs_dances.id'))
    # Delete when dance is deleted
    dance = db.relationship(Dance, backref=db.backref("songs_songs", uselist=True, cascade='delete,all'))
    creation_user_id = db.Column(db.Integer, db.ForeignKey("users_user.id"))
    # Delete when user is deleted
    creation_user = db.relationship(User, backref=db.backref("songs_songs", uselist=True, cascade='delete,all'))

    def get_rating(self):
        return sum(rating.value for rating in Rating.query.filter_by(song_id=self.id).all() if rating.value > 0)

    def get_user_rating(self, user):
        query = Rating.query.filter_by(song_id=self.id, user_id=user.id)
        if query.count() > 0:
            return query.one().value
        else:
            return -1

    def get_user_rating_as_string(self, user):
        user_rating = self.get_user_rating(user)

        if user_rating > 0:
            return user_rating
        else:
            return "nr"

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
    user_id = db.Column(db.Integer, db.ForeignKey("users_user.id"))
    # Delete when user is deleted
    user = db.relationship(User, backref=db.backref("songs_ratings", uselist=True, cascade='delete,all'))
    song_id = db.Column(db.Integer, db.ForeignKey("songs_songs.id"))
    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref("songs_ratings", uselist=True, cascade='delete,all'))

    # FIXME: Constraint on double voting!

    def __init__(self, user, song):
        self.song_id = song.id
        self.user_id = user.id
