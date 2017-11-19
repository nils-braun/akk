from wtforms import StringField, Field
from wtforms.widgets import TextInput, Input, HTMLString


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