import random
from datetime import datetime, timedelta

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
            dance = Dance()
            dance.name=dance_name
            db.session.add(dance)
            db.session.commit()

            dance_created_new = True

        return dance, dance_created_new


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
            artist = Artist()
            artist.name=artist_name
            db.session.add(artist)
            db.session.commit()

            artist_created_new = True

        return artist, artist_created_new


class Label(db.Model):
    __tablename__ = "songs_labels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(150), unique=True)
    color = db.Column(db.Unicode(6))

    @staticmethod
    def get_or_add_label(label_name):
        label = Label.query.filter_by(name=label_name).first()
        label_created_new = False
        if not label:
            label = Label()
            label.name = label_name
            label.color = random.choice(["#db56b2", "#dbc256", "#db5e56", "#91db56",
                                         "#56db7f", "#56d3db", "#566fdb", "#a056db"])
            db.session.add(label)
            db.session.commit()

            label_created_new = True

        return label, label_created_new


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

    @staticmethod
    def get_rating(rating):
        if rating is not None:
            return "%d" % round(rating)
        else:
            return SONGS.NOT_RATED_STRING

    def get_user_rating(self, user):
        query = Rating.query.filter_by(song_id=self.id, user_id=user.id)
        if query.count() > 0:
            return query.one().value
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

    @staticmethod
    def set_add_or_delete_rating(song, user, rating_value):
        query = Rating.query.filter_by(song_id=song.id, user_id=user.id)

        if int(rating_value) != 0:
            # There is a rating
            if query.count() == 0:
                # Add new rating
                new_rating = Rating()
                new_rating.song_id = song.id
                new_rating.user_id = user.id
                new_rating.value = rating_value

                db.session.add(new_rating)
            else:
                # Update old rating
                old_rating = query.one()
                old_rating.value = rating_value
                db.session.merge(old_rating)
        else:
            if query.count() > 0:
                for rating_to_delete in query.all():
                    db.session.delete(rating_to_delete)

        db.session.commit()


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

    @staticmethod
    def set_or_add_comment(song, user, note_value):
        if note_value.strip() == "":
            # Do not add empty comments
            return

        query = Comment.query.filter_by(song_id=song.id, user_id=user.id)

        if query.count() == 0:
            # Add new rating
            new_comment = Comment()
            new_comment.song_id = song.id
            new_comment.user_id = user.id
            new_comment.creation_date = datetime.now()
            new_comment.note = note_value

            db.session.add(new_comment)
        else:
            # Update old rating
            old_comment = query.one()
            old_comment.note = note_value
            db.session.merge(old_comment)

        db.session.commit()


class LabelsToSongs(db.Model):
    __tablename__ = "songs_labels_to_songs"
    song_id = db.Column(db.Integer, db.ForeignKey(Song.__tablename__ + ".id"), primary_key=True)
    label_id = db.Column(db.Integer, db.ForeignKey(Label.__tablename__ + ".id"), primary_key=True)

    # Delete when song is deleted
    song = db.relationship(Song, backref=db.backref(__tablename__, uselist=True, cascade="delete,all"))
    # Delete when label is deleted
    label = db.relationship(Label, backref=db.backref(__tablename__, uselist=True, cascade="delete,all"))
