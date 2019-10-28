from flask_wtf.file import FileRequired, FileAllowed
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL, Optional, InputRequired, Email
from validators import RequiredIf, NotRequiredIf

ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar', 'gz'}


class SubmitJob(Form):
    email = StringField('Email Address',
                        description="When job is complete this e-mail will receive the download links",
                        render_kw={
                            "autofocus": "",
                            "value": "eb167@nyu.edu"
                        },
                        validators=[
                            # Optional()
                            InputRequired(),
                            Email()
                        ])

    chrom = StringField('chrom',
                        description="ID of the chromosome to modify",
                        render_kw={
                            "value": "X"
                        },
                        validators=[
                            # Optional()
                            InputRequired()
                        ])

    # POSITION
    position = StringField('position',
                           description="Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end "
                                       "of chromosome. Note: Position is 0-based",
                           render_kw={
                               "value": "3"
                           },
                           validators=[Optional()])
    # OR
    upstream_fasta = FileField('upstream_fasta',
                               description="FASTA file with upstream sequence.",
                               # validators=[Optional()])
                               validators=[
                                   RequiredIf("position", message="error")
                               ])
    downstream_fasta = FileField('downstream_fasta',
                                 description="FASTA file with downstream sequence.",
                                 # validators=[Optional()])
                                 validators=[
                                     RequiredIf("position", message="error")
                                 ])

    # Uploads
    in_fasta = FileField('in_fasta',
                         description="File of new sequence to be inserted into reference genome in FASTA format.",
                         # validators=[Optional()])
                         validators=[
                             # FileRequired(),
                             # FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type')
                         ])
    in_gff = FileField('in_gff',
                       description="GFF file describing new FASTA sequence to be inserted.",
                       # validators=[Optional()])
                       validators=[
                           # FileRequired(),
                           # FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type')
                       ])
    # Downloads
    ref_fasta = StringField('ref_fasta',
                            description="Path to reference FASTA file.",
                            render_kw={
                                "placeholder": "Enter Reference URL",
                                "value": "https://raw.githubusercontent.com/gencorefacility/reform/master/test_data/7/ref.fa"
                            },
                            # validators=[Optional()])
                            validators=[
                                URL(),
                                InputRequired()
                            ])
    ref_gff = StringField('ref_gff',
                          description="Path to reference gff file.",
                          render_kw={
                              "placeholder": "Enter Reference URL",
                              "value": "https://raw.githubusercontent.com/gencorefacility/reform/master/test_data/7/ref.gtf"
                          },
                          # validators=[Optional()])
                          validators=[
                              URL(),
                              InputRequired()
                          ])
