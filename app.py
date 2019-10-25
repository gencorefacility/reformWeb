import datetime
import os
import wget

from flask import Flask, render_template, request, flash, url_for
from werkzeug.utils import redirect
from werkzeug.utils import secure_filename

from forms import SubmitJob

app = Flask(__name__)
# TODO: Move this secret_key out
app.secret_key = 'development key'

# TODO: Remove when going into production

if os.name == 'nt':  # If Windows
    UPLOAD_FOLDER = 'uploads'
else:
    UPLOAD_FOLDER = './uploads'

UPLOAD_FILES = ['upstream_fasta', 'downstream_fasta', 'in_fasta', 'in_gff']
DOWNLOAD_FILES = ['ref_fasta', 'ref_gff']
ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar', 'gz'}


@app.route('/', methods=['GET', 'POST'])
def submit():
    form = SubmitJob(request.form)
    if request.method == 'POST' and form.validate():
        # User Submits Job #
        # (1) Create unique ID for each submission
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        targetDir = os.path.join(UPLOAD_FOLDER, timestamp)

        # (2) Upload files from user device to server
        # Verify all files are present before uploading
        for files in UPLOAD_FILES:
            verified = verify_uploads(files)
            if not verified:
                break
        # Upload Files to UPLOAD_DIR/timestamp/
        if verified:
            for files in UPLOAD_FILES:
                upload(targetDir, files)

        # (3) Download files from user provided URLs to server
        for files in DOWNLOAD_FILES:
            download(targetDir, files)

        flash('Job Submitted')
        return redirect(url_for('submit'))
    return render_template('index.html', form=form)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def verify_uploads(file):
    fileObj = request.files[file]

    if fileObj.filename == '':
        flash('No ' + file + ' file selected for uploading', 'error')
        return False
    if fileObj and allowed_file(fileObj.filename):
        return True
    else:
        flash('Invalid File Type for ' + file)
        return False


def upload(targetDir, file):
    fileObj = request.files[file]
    # make the directory based on timestamp
    os.system('mkdir ' + targetDir)
    # save the file
    fileObj.save(os.path.join(targetDir,
                              secure_filename(fileObj.filename)))


def download(targetDir, file):
    file = request.form[file]
    if file:
        print("targetDir = " + targetDir)
        wget.download(file, targetDir)


def runReform():
    command = 'python reform.py --chrom {} --position {} --in_fasta {} --in_gff {} --ref_fasta {} --ref_gff {}'.format(
        request.form['chrom'],
        request.form['position'],
        os.path.join(UPLOAD_FOLDER, secure_filename(in_fasta.filename)),
        os.path.join(UPLOAD_FOLDER, secure_filename(in_gff.filename)),
        ref_fasta_download,
        ref_gff_download)
    print(command)
    os.system(command)


if __name__ == '__main__':
    app.run(debug=True)
