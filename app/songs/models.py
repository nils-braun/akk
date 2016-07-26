from app import db


class Dance(db.Model):
    """
    Class representing a dance type.
    """
    __tablename__ = 'songs_dances'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)

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
    name = db.Column(db.String(250), unique=True, nullable=False)

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
    title = db.Column(db.String(350), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('songs_artists.id'))
    # Delete when artists is deleted
    artist = db.relationship(Artist, backref=db.backref("songs_songs", uselist=True, cascade='delete,all'))
    dance_id = db.Column(db.Integer, db.ForeignKey('songs_dances.id'))
    # Delete when dance is deleted
    dance = db.relationship(Dance, backref=db.backref("songs_songs", uselist=True, cascade='delete,all'))

    def __init__(self, title, artist, dance):
        """
        Create a new song.
        """
        self.title = title
        self.artist_id = artist.id
        self.dance_id = dance.id

    def __repr__(self):
        return "Song: {self.title} ({self.id}) - {self.artist} - {self.dance}".format(self=self)

