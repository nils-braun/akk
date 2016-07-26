from flask_wtf import Form
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class DeleteArtistForm(Form):
    """
    Form to delete an artist and every attached song.
    """
    name = StringField('Artist Name', [DataRequired()])


class DeleteDanceForm(Form):
    """
    Form to delete a dance and every attached song.
    """
    name = StringField('Dance Name', [DataRequired()])


class CreateSongForm(Form):
    """
    Form to create a new song.
    """
    title = StringField('Song Title', [DataRequired()])
    artist_name = StringField('Artist', [DataRequired()])
    dance_name = StringField('Dance', [DataRequired()])


class EditSongForm(CreateSongForm):
    """
    Refined form for editing songs.
    """
    edit_button = SubmitField()
    delete_button = SubmitField()
    song_id = HiddenField(default=None)
