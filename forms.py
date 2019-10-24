from flask_wtf.file import FileRequired
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL


class SubmitJob(Form):
    email = StringField('Email Address', [
        validators.Length(min=6, max=35),
        validators.Email(message="invalid e-mail")
    ])
    chrom = StringField('chrom', [validators.DataRequired(message="")])
    position = StringField('position', [validators.DataRequired(message="")])

    # Uploads
    in_fasta = FileField('in_fasta', validators=[FileRequired()])
    in_gff = FileField('in_gff', validators=[FileRequired()])

    # Downloads
    ref_fasta = StringField('ref_fasta', validators=[URL()])
    ref_gff = StringField('ref_gff', validators=[URL()])
