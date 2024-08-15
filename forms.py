from wtforms import Form, StringField, FileField
from wtforms.validators import URL, Optional, InputRequired, Email
from flask_wtf.file import FileRequired, FileAllowed

ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar', 'gz'}

# Use it for production site
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
                            description="URL to reference FASTA file. e.g. ftp://ftp.ensembl.org/pub/release-88/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.toplevel.fa.gz",
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

# Use it for test site (test_case_1)
class Testjob(Form):
    email = StringField('Email Address',
                        description="When job is complete this e-mail will receive the download links",
                        render_kw={
                            "autofocus": "",
                        },
                        validators=[
                            InputRequired(),
                            Email()
                        ],
                        default="ys4680@nyu.edu") # hard code email

    chrom = StringField('Chromosome',
                        description="ID of the chromosome to modify. Must match ID in FASTA file.",
                        validators=[
                            InputRequired()
                        ],
                        default = "X") # Chromosome has been set to X as default

    # POSITION
    position = StringField('Position',
                           description="Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end "
                                       "of chromosome. Note: Position is 0-based",
                           validators=[Optional()])
    # OR
    upstream_fasta = FileField('Upstream Sequence',
                               description="FASTA file with upstream sequence. If no file is selected, the system will use 'test-up.fa' as a default.",
                               validators=[
                                   Optional()
                               ])
    downstream_fasta = FileField('Downstream Sequence',
                                 description="FASTA file with downstream sequence. If no file is selected, the system will use 'test-down.fa' as a default.",
                                 validators=[
                                     Optional()
                                 ])

    # Uploads
    in_fasta = FileField('Inserted Sequence (FASTA)',
                         description="Please upload the new sequence to be inserted into the reference genome. If no file is selected, the system will use 'test-in.fa' as a default.",
                         validators=[
                             Optional(),
                             FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                             # FileRequired()
                         ])
    in_gff = FileField('Inserted Reference (gff3 or gtf)',
                       description="Please upload the GFF file describing the new FASTA sequence to be inserted. If no file is selected, the system will use 'test-in.gff' as a default.",
                       validators=[
                           Optional(),
                           FileAllowed([ALLOWED_EXTENSIONS], 'Invalid File Type'),
                          # InputRequired()
                       ])
    # Downloads
    ref_fasta = StringField('Reference Sequence (FASTA)',
                            description="URL to reference FASTA file. e.g. ftp://ftp.ensembl.org/pub/release-88/fasta/mus_musculus/dna/Mus_musculus.GRCm38.dna.toplevel.fa.gz",
                            render_kw={
                                "placeholder": "Enter Reference URL",
                            },
                            validators=[
                                URL(),
                                InputRequired()
                            ],
                            default = "test-ref.fa")
    
    ref_gff = StringField('Reference Annotation (gff3 or gtf)',
                          description="URL to reference gff file. e.g. ftp://ftp.ensembl.org/pub/release-88/gff3/mus_musculus/Mus_musculus.GRCm38.88.gff3.gz",
                          render_kw={
                              "placeholder": "Enter Reference URL",
                          },
                          validators=[
                              URL(),
                              InputRequired()
                          ],
                          default = "test-ref.gtf")
