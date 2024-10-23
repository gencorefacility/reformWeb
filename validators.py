from flask_wtf.file import FileRequired
from wtforms.validators import InputRequired, DataRequired


class RequiredIf(FileRequired):
    """Validator which makes a field required if another field is set and has a truthy value.

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms

    """
    field_flags = ('requiredif',)

    def __init__(self, other_field_name, message=None, *args, **kwargs):
        self.other_field_name = other_field_name
        self.message = message

    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)


class NotRequiredIf(FileRequired):
    """Validator which makes a field required if another field is set and has a truthy value.

    Sources:
        - http://wtforms.simplecodes.com/docs/1.0.1/validators.html
        - http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms

    """
    field_flags = ('notrequiredif',)

    def __init__(self, other_field_name, message=None, *args, **kwargs):
        self.other_field_name = other_field_name
        self.message = message

    def __call__(self, form, field):
        other_field = form[self.other_field_name]
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if not bool(other_field.data):
            super(NotRequiredIf, self).__call__(form, field)

class FileNotEmpty(object):
    """
    Validates that the uploaded file is not empty.
    """

    def __init__(self, message=None):
        if not message:
            message = "The file should be non-empty."
        self.message = message

    def __call__(self, form, field):
         for uploaded_file in field.data:
            if uploaded_file.data.getbuffer().nbytes == 0:  # Check file size
                raise Exception(uploaded_file.filename + "is empty, please check the file content")