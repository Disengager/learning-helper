from wtforms.fields.core import SelectField


class CustomSelectField(SelectField):
    def pre_validate(self, form):
        pass