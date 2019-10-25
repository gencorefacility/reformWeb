import os

import wget
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

if os.name == 'nt':
    UPLOAD_FOLDER = 'uploads'
else:
    UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar.gz', 'tar', 'gz'}

app.secret_key = 'super secret key'


@app.route('/')
@app.route('/submit')
def upload_file():
    return render_template('submit.html')


@app.route('/submitted', methods=['GET', 'POST'])
def grab():
    if request.method == 'POST':
        if os.name == 'nt':  # Windows
            os.system('rd /s /q uploads')
            os.system('mkdir uploads')
        else:
            os.system('rm ./uploads/*')

    # Upload Files
    upstream_fasta = request.files['upstream_fasta']
    upstream_fasta.save(os.path.join(UPLOAD_FOLDER, secure_filename(upstream_fasta.filename)))

    downstream_fasta = request.files['downstream_fasta']
    downstream_fasta.save(os.path.join(UPLOAD_FOLDER, secure_filename(downstream_fasta.filename)))

    in_fasta = request.files['in_fasta']
    in_fasta.save(os.path.join(UPLOAD_FOLDER, secure_filename(in_fasta.filename)))

    in_gff = request.files['in_gff']
    in_gff.save(os.path.join(UPLOAD_FOLDER, secure_filename(in_gff.filename)))

    # Download from links
    ref_fasta_url = request.form['ref_fasta']
    ref_fasta_download = wget.download(ref_fasta_url, UPLOAD_FOLDER)

    ref_gff_url = request.form['ref_gff']
    ref_gff_download = wget.download(ref_gff_url, UPLOAD_FOLDER)

    command = 'python reform.py --chrom {} --position {} --in_fasta {} --in_gff {} --ref_fasta {} --ref_gff {}'.format(
        request.form['chrom'],
        request.form['position'],
        os.path.join(UPLOAD_FOLDER, secure_filename(in_fasta.filename)),
        os.path.join(UPLOAD_FOLDER, secure_filename(in_gff.filename)),
        ref_fasta_download,
        ref_gff_download)
    print(command)
    os.system(command)

    return 'job submitted'


if __name__ == '__main__':
    app.run(debug=True)
