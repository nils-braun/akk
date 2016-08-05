from flask_wtf import Form
from wtforms import StringField, SubmitField, HiddenField, IntegerField, TextAreaField
from wtforms.fields.core import BooleanField
from wtforms.validators import DataRequired
from wtforms.widgets.core import TextInput


class CompletionInput(TextInput):
    def __init__(self, column):
        self.column = column
        super(CompletionInput, self).__init__()

    def __call__(self, field, **kwargs):
        class_string = " completion completion-{column}".format(column=self.column)
        if "class" in kwargs:
            kwargs["class"] += class_string
        else:
            kwargs["class"] = class_string

        return super(TextInput, self).__call__(field, **kwargs)

class CompletionField(StringField):

    def __init__(self, *args, **kwargs):
        if "column" in kwargs:
            column = kwargs.pop("column")
        else:
            column = "all"
        super(CompletionField, self).__init__(*args, widget=CompletionInput(column=column), **kwargs)


class SearchSongForm(Form):
    query = CompletionField(column="all")


class DeletionForm(Form):
    """
    Form to delete a dance or an artist and every attached song.
    """
    sure_to_delete = SubmitField("Force delete")
    unsure_to_delete = SubmitField("Show Usage")

class DeleteArtistForm(DeletionForm):
    """
    Form to delete an artist and every attached song.
    """
    name = CompletionField('Artist Name', [DataRequired()], column="artist")


class DeleteDanceForm(DeletionForm):
    """
    Form to delete a dance and every attached song.
    """
    name = CompletionField('Dance Name', [DataRequired()], column="dance")


class CreateSongForm(Form):
    """
    Form to create a new song.
    """
    title = StringField('Song Title', [DataRequired()])
    artist_name = CompletionField('Artist', [DataRequired()], column="artist")
    dance_name = CompletionField('Dance', [DataRequired()], column="dance")


class EditSongForm(CreateSongForm):
    """
    Refined form for editing songs.
    """
    rating = StringField()
    note = TextAreaField()
    edit_button = SubmitField()
    delete_button = SubmitField()
    path = StringField("Path")
    song_id = HiddenField(default=None)
