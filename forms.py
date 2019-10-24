from flask_wtf.file import FileRequired
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL, Optional, InputRequired
from validators import RequiredIf, NotRequiredIf


class SubmitJob(Form):
    email = StringField('Email Address', [
        validators.InputRequired(),
        validators.Email(message="invalid e-mail")
    ])

    chrom = StringField('chrom', [validators.InputRequired(message="")])

    # POSITION
    position = StringField('position', validators=[NotRequiredIf('downstream_fasta')])
    #OR
    upstream_fasta = FileField('upstream_fasta', validators=[NotRequiredIf('downstream_fasta')])
    downstream_fasta = FileField('downstream_fasta', validators=[NotRequiredIf('upstream_fasta')])

    # Uploads
    in_fasta = FileField('in_fasta', validators=[Optional()])
    in_gff = FileField('in_gff', validators=[Optional()])

    # Downloads
    ref_fasta = StringField('ref_fasta', validators=[URL(), Optional()])
    ref_gff = StringField('ref_gff', validators=[URL(), Optional()])
