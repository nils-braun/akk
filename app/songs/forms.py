from flask_wtf import Form
from wtforms import StringField, SubmitField, HiddenField, TextAreaField, Field, FileField
from wtforms.fields.core import IntegerField
from wtforms.validators import DataRequired, regexp
from wtforms.widgets.core import TextInput, HTMLString, Input


class TagsInput(TextInput):
    def __call__(self, field, **kwargs):
        class_string = " tags"
        if "class" in kwargs:
            kwargs["class"] += class_string
        else:
            kwargs["class"] = class_string

        return super(TextInput, self).__call__(field, **kwargs)


class TagsField(StringField):
    def __init__(self, *args, **kwargs):
        super(TagsField, self).__init__(*args, widget=TagsInput(), **kwargs)


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


class RatingInput(Input):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('class', "rating")
        kwargs['data-value'] = field._value()
        kwargs['data-enabled'] = True
        return HTMLString('<div %s></div>' % self.html_params(name=field.name, **kwargs))


class RatingField(Field):
    widget = RatingInput()

    def _value(self):
        return self.data if self.data not in ["nr", None] else 0


class EntityEditForm(Form):
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


class CreateSongForm(Form):
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
