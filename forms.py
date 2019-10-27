from flask_wtf.file import FileRequired
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL, Optional, InputRequired
from validators import RequiredIf, NotRequiredIf


class SubmitJob(Form):
    email = StringField('Email Address',
                        description="When job is complete this e-mail will receive the download links",
                        render_kw={"size": 30, "autofocus": ""},
                        validators=[Optional()])

    chrom = StringField('chrom',
                        description="ID of the chromosome to modify",
                        validators=[Optional()])

    # POSITION
    position = StringField('position',
                           description="Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end "
                                       "of chromosome. Note: Position is 0-based",
                           validators=[Optional()])
    # OR
    upstream_fasta = FileField('upstream_fasta',
                               description="FASTA file with upstream sequence.",
                               validators=[Optional()])
    # validators=[NotRequiredIf("position", message="error")])

    downstream_fasta = FileField('downstream_fasta',
                                 description="FASTA file with downstream sequence.",
                                 validators=[Optional()])
    # validators=[NotRequiredIf("position", message="error")])

    # Uploads
    in_fasta = FileField('in_fasta',
                         description="File of new sequence to be inserted into reference genome in FASTA format.",
                         validators=[Optional()])
    in_gff = FileField('in_gff',
                       description="GFF file describing new FASTA sequence to be inserted.",
                       validators=[Optional()])

    # Downloads
    ref_fasta = StringField('ref_fasta',
                            description="Path to reference FASTA file.",
                            render_kw={"size": 100, "placeholder": "Enter Reference URL"},
                            validators=[Optional()])
    # validators = [URL(), validators.InputRequired()]
    ref_gff = StringField('ref_gff',
                          description="Path to reference gff file.",
                          render_kw={"size": "100%", "placeholder": "Enter Reference URL"},
                          validators=[Optional()])
    # validators = [URL(), validators.InputRequired()]
