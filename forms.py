from flask_wtf.file import FileRequired
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL, Optional, InputRequired
from validators import RequiredIf, NotRequiredIf


class SubmitJob(Form):
    email = StringField('Email Address', validators=[Optional()])

    chrom = StringField('chrom', validators=[Optional()])

    # POSITION
    position = StringField('position', validators=[Optional()])
    # OR
    upstream_fasta = FileField('upstream_fasta', validators=[NotRequiredIf("position", message="hey!")])
    downstream_fasta = FileField('downstream_fasta', validators=[NotRequiredIf("position", message="ho!")])

    # Uploads
    in_fasta = FileField('in_fasta', validators=[Optional()])
    in_gff = FileField('in_gff', validators=[Optional()])

    # Downloads
    # ref_fasta = StringField('ref_fasta', validators=[URL(), validators.InputRequired()])
    # ref_gff = StringField('ref_gff', validators=[URL(), validators.InputRequired()])
    # Downloads
    ref_fasta = StringField('ref_fasta', validators=[Optional()], render_kw={"placeholder": "Enter Reference URL"},
                            description="Ale was here")
    ref_gff = StringField('ref_gff', validators=[Optional()], render_kw={"placeholder": "Enter Reference URL"})
