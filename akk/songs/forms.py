from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, TextAreaField, FileField, IntegerField
from wtforms.validators import DataRequired

from akk.common.forms import TagsField, CompletionField, RatingField


class EntityEditForm(FlaskForm):
    """
    Form to delete a dance or an artist and every attached song.
    """
    sure_to_delete = SubmitField("Force delete")
    unsure_to_delete = SubmitField("Show Usage")
    rename = SubmitField("Rename")
    rename_name = StringField("New name")


class EditArtistForm(EntityEditForm):
    """
    Form to delete an artist and every attached song.
    """
    name = CompletionField('Artist Name', [DataRequired()], column="artist")


class EditDanceForm(EntityEditForm):
    """
    Form to delete a dance and every attached song.
    """
    name = CompletionField('Dance Name', [DataRequired()], column="dance")


class CreateSongForm(FlaskForm):
    """
    Form to create a new song.
    """
    title = StringField('Song Title', [DataRequired()])
    artist_name = CompletionField('Artist', [DataRequired()], column="artist")
    dance_name = CompletionField('Dance', [DataRequired()], column="dance")
    path = FileField("Path")
    bpm = IntegerField("BPM", default=0)
    labels = TagsField('Tags')


class EditSongForm(CreateSongForm):
    """
    Refined form for editing songs.
    """
    rating = RatingField()
    note = TextAreaField()
    edit_button = SubmitField()
    delete_button = SubmitField()
    song_id = HiddenField(default=None)
