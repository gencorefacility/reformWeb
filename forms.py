from wtforms import Form, StringField, FileField
from wtforms.validators import URL, Optional, InputRequired, Email
from flask_wtf.file import FileRequired, FileAllowed

ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar', 'gz'}


class SubmitJob(Form):
    email = StringField('Email Address',
                        description="When job is complete this e-mail will receive the download links",
                        render_kw={
                            "autofocus": "",
                        },
                        validators=[
                            InputRequired(),
                            Email()
                        ])

    chrom = StringField('Chromosome',
                        description="ID of the chromosome to modify. Must match ID in FASTA file.",
                        validators=[
                            InputRequired()
                        ])

    # POSITION
    position = StringField('Position',
                           description="Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end "
                                       "of chromosome. Note: Position is 0-based",
                           validators=[Optional()])
    # OR
    upstream_fasta = FileField('Upstream Sequence',
                               description="FASTA file with upstream sequence.",
                               validators=[
                                   Optional()
                               ])
    downstream_fasta = FileField('Downstream Sequence',
                                 description="FASTA file with downstream sequence.",
                                 validators=[
                                     Optional()
                                 ])

    # Uploads
    in_fasta = FileField('Inserted Sequence (FASTA)',
                         description="New sequence to be inserted into reference genome.",
                         validators=[
                             Optional(),
                             FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                             FileRequired()
                         ])
    in_gff = FileField('Inserted Reference (gff3 or gtf)',
                       description="GFF file describing new FASTA sequence to be inserted.",
                       validators=[
                           Optional(),
                           FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                           InputRequired()
                       ])
    # Downloads
    ref_fasta = StringField('Reference Sequence (FASTA)',
                            description="URL to reference FASTA file. e.g. ftp://ftp.ensembl.org/pub/release-88/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.toplevel.fa.gz"",
                            render_kw={
                                "placeholder": "Enter Reference URL",
                            },
                            validators=[
                                URL(),
                                InputRequired()
                            ])
    ref_gff = StringField('Reference Annotation (gff3 or gtf)',
                          description="URL to reference gff file. e.g. ftp://ftp.ensembl.org/pub/release-88/gff3/mus_musculus/Mus_musculus.GRCm38.88.gff3.gz",
                          render_kw={
                              "placeholder": "Enter Reference URL",
                          },
                          validators=[
                              URL(),
                              InputRequired()
                          ])
