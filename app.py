import datetime
import os
import subprocess

import wget

from flask import Flask, render_template, request, flash, url_for, send_file, Markup
from werkzeug.utils import redirect
from werkzeug.utils import secure_filename

from forms import SubmitJob
import sqlite3

from flask_mail import Mail, Message

app = Flask(__name__)
# TODO: Move this secret_key out
app.secret_key = 'development key'

app.config['MAIL_SERVER'] = 'smtp.nyu.edu'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = 'reform-test@nyu.edu'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# TODO: Remove when going into production
if os.name == 'nt':  # If Windows
    UPLOAD_FOLDER = 'uploads'
else:
    UPLOAD_FOLDER = './uploads'

UPLOAD_FILES = ['in_fasta', 'in_gff']
DOWNLOAD_FILES = ['ref_fasta', 'ref_gff']
ALLOWED_EXTENSIONS = {'fa', 'gff', 'gff3', 'gtf', 'fasta', 'fna', 'tar', 'gz'}


@app.route('/', methods=['GET', 'POST'])
def submit():
    form = SubmitJob(request.form)
    if request.method == 'POST' and form.validate():
        if (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename) and request.form[
            'position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit'))
        if request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename:
            flash("Error: Must enter both upstream and downstream", 'error')
            return redirect(url_for('submit'))
        if not (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename) and not \
                request.form['position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit'))
        else:
            # User Submits Job #
            # (1) Create unique ID for each submission
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            target_dir = os.path.join(UPLOAD_FOLDER, timestamp)
            # (2) Log to Database
            status = "submitted"
            if not os.path.isfile('database.db'):
                create_db()

            try:
                with sqlite3.connect("database.db") as con:
                    cur = con.cursor()
                    cur.execute(
                        'INSERT INTO submissions (timestamp, email, status, chrom, upstream_fasta, downstream_fasta, '
                        'position, ref_fasta, ref_gff, in_fasta, in_gff ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (timestamp,
                         request.form['email'],
                         status,
                         request.form['chrom'],
                         request.files[
                             'upstream_fasta'].filename,
                         request.files[
                             'downstream_fasta'].filename,
                         request.form['position'],
                         request.form['ref_fasta'],
                         request.form['ref_gff'],
                         request.files[
                             'in_fasta'].filename,
                         request.files[
                             'in_gff'].filename))

                    con.commit()
                    flash("Record successfully added", 'debug')
            except:
                con.rollback()
                flash("error in insert operation", 'error')

            # (3) Upload files from user device to server
            # Verify all files are present before uploading
            for files in UPLOAD_FILES:
                verified = verify_uploads(files)
                if not verified:
                    return redirect(url_for('submit'))

            # Upload Files to UPLOAD_DIR/timestamp/
            if verified:
                for files in UPLOAD_FILES:
                    upload(target_dir, files)

            if not request.form['position'] and request.files['upstream_fasta'].filename and request.files[
                'downstream_fasta'].filename:
                upload(target_dir, 'upstream_fasta')
                upload(target_dir, 'downstream_fasta')

            # (4) Download files from user provided URLs to server
            ref_fasta = download(target_dir, 'ref_fasta')
            ref_gff = download(target_dir, 'ref_gff')

            # (5) Run the reform.py
            try:
                flash(u'Job ' + timestamp + ' submitted', 'info')
                runReform(target_dir, ref_fasta, ref_gff, timestamp)

                send_email(request.form['email'], timestamp)

                flash(Markup('click <a href="./download/' + timestamp + '">here to download</a>'), 'info')

                con.execute("UPDATE submissions SET status=? where timestamp=? ", ("complete", timestamp))
                con.commit()
                con.close()
                return redirect(url_for('submit'))

            except:
                flash(u'Job ' + timestamp + ' failed', 'error')
                con.execute("UPDATE submissions SET status=? where timestamp=?", ("failed", timestamp))
                con.commit()
                con.close()

    return render_template('form.html', form=form)


@app.route('/download/<timestamp>')
def downloadFile(timestamp):
    try:
        path = "./results/" + timestamp + "/" + timestamp + ".tar.gz"
        return send_file(path, as_attachment=True)
    except:
        flash(Markup('click <a href="./download/' + timestamp + '">here to download</a>'), 'info')
        flash("Download Error: File does not exist - " + path, 'error')
        return redirect(url_for('submit'))


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
        flash('Invalid File Type for ' + file, 'error')
        return False


def upload(target_dir, file):
    fileObj = request.files[file]
    # make the directory based on timestamp
    os.system('mkdir ' + target_dir)
    # save the file
    fileObj.save(os.path.join(target_dir,
                              secure_filename(fileObj.filename)))


def download(target_dir, file):
    URL = request.form[file]
    if URL:
        return wget.download(URL, target_dir)


def runReform(target_dir, ref_fasta, ref_gff, timestamp):
    os.system("mkdir results/" + timestamp)
    if request.form['position']:
        command = 'python reform.py --chrom {} --position {} --in_fasta {} --in_gff {} --ref_fasta {} --ref_gff {} ' \
                  '--output_dir {}'.format(
            request.form['chrom'],
            request.form['position'],
            os.path.join(target_dir, secure_filename(request.files['in_fasta'].filename)),
            os.path.join(target_dir, secure_filename(request.files['in_gff'].filename)),
            ref_fasta,
            ref_gff,
            "./results/" + timestamp + "/"
        )
    else:
        command = 'python reform.py --chrom {} --upstream_fasta {} --downstream_fasta {} --in_fasta {} --in_gff {} ' \
                  '--ref_fasta {} --ref_gff {} --output_dir {}'.format(
            request.form['chrom'],
            os.path.join(target_dir, secure_filename(request.files['upstream_fasta'].filename)),
            os.path.join(target_dir, secure_filename(request.files['downstream_fasta'].filename)),
            os.path.join(target_dir, secure_filename(request.files['in_fasta'].filename)),
            os.path.join(target_dir, secure_filename(request.files['in_gff'].filename)),
            ref_fasta,
            ref_gff,
            "./results/" + timestamp + "/"
        )
    flash(command, 'debug')

    output = subprocess.getoutput(command)
    print("OUTPUT IS " + output + "<-------")
    # os.system(command)

    os.system('tar -czf results/' + timestamp + '/' + timestamp + '.tar.gz -C results/' + timestamp + '/ .')


def create_db():
    conn = sqlite3.connect('database.db')
    conn.execute(
        'CREATE TABLE submissions (timestamp TEXT, email TEXT, status TEXT, chrom TEXT, upstream_fasta TEXT, '
        'downstream_fasta TEXT, position TEXT, ref_fasta TEXT, ref_gff TEXT, in_fasta TEXT, in_gff TEXT)')
    conn.close()


def send_email(email, timestamp):
    msg = Message('reform results', sender='reform-test@nyu.edu', recipients=[email])
    print("TIMESTAMP=" + timestamp)
    msg.html = "reform job complete. <a href='http://localhost:5000/download/" + timestamp + "'> Click here to download " \
                                                                                             "results.</a> "
    mail.send(msg)


if __name__ == '__main__':
    app.run(debug=True)
