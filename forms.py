from flask_wtf.file import FileRequired, FileAllowed
from wtforms import FileField
from wtforms import Form, StringField, validators
from wtforms.validators import URL, Optional, InputRequired, Email, DataRequired
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

    chrom = StringField('Chromosome',
                        description="ID of the chromosome to modify",
                        render_kw={
                            "value": "X"
                        },
                        validators=[
                            # Optional()
                            InputRequired()
                        ])

    # POSITION
    position = StringField('Position',
                           description="Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end "
                                       "of chromosome. Note: Position is 0-based",
                           render_kw={
                               "value": "3"
                           },
                           validators=[Optional()])
    # OR
    upstream_fasta = FileField('Upstream Sequence',
                               description="FASTA file with upstream sequence.",
                               # validators=[Optional()])
                               validators=[
                                   # NotRequiredIf("position", message="error")
                                   Optional()
                               ])
    downstream_fasta = FileField('Downstream Sequence',
                                 description="FASTA file with downstream sequence.",
                                 # validators=[Optional()])
                                 validators=[
                                     # NotRequiredIf("position", message="error")
                                     Optional()
                                 ])

    # Uploads
    in_fasta = FileField('Inserted Sequence (FASTA)',
                         description="New sequence to be inserted into reference genome.",
                         # validators=[Optional()])
                         validators=[
                             Optional(),
                             FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                             FileRequired()
                         ])
    in_gff = FileField('Inserted Reference (gff3 or gtf)',
                       description="GFF file describing new FASTA sequence to be inserted.",
                       # validators=[Optional()])
                       validators=[
                           Optional(),
                           FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                           InputRequired()
                       ])
    # Downloads
    ref_fasta = StringField('Reference Sequence (FASTA)',
                            description="URL to reference FASTA file.",
                            render_kw={
                                "placeholder": "Enter Reference URL",
                                "value": "https://raw.githubusercontent.com/gencorefacility/reform/master/test_data/7/ref.fa"
                            },
                            # validators=[Optional()])
                            validators=[
                                URL(),
                                InputRequired()
                            ])
    ref_gff = StringField('Reference Annotation (gff3 or gtf)',
                          description="URL to reference gff file.",
                          render_kw={
                              "placeholder": "Enter Reference URL",
                              "value": "https://raw.githubusercontent.com/gencorefacility/reform/master/test_data/7/ref.gtf"
                          },
                          # validators=[Optional()])
                          validators=[
                              URL(),
                              InputRequired()
                          ])
