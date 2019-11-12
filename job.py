import os
import sqlite3

import wget
from flask import request, flash
from flask_mail import Message, Mail
from werkzeug.utils import secure_filename

from app import ALLOWED_EXTENSIONS, app

app.config['MAIL_SERVER'] = 'smtp.nyu.edu'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = 'reform-test@nyu.edu'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)


def redisjob(target_dir, timestamp, email, chrom, upstream_fasta, downstream_fasta, position, ref_fastaURL, ref_gffURL,
             in_fasta, in_gff):
    # (4) Download files from user provided URLs to server
    try:
        ref_fasta = download(target_dir, ref_fastaURL)
        ref_gff = download(target_dir, ref_gffURL)
    except Exception as e:
        # TODO: e-mal of failure
        print("ERROR: " + e)
        update_db(timestamp, "failed to download references")

    # (5) Run the reform.py
    try:
        runReform(target_dir, ref_fasta, ref_gff, timestamp, position, chrom, in_fasta, in_gff, upstream_fasta,
                  downstream_fasta)
        send_email(email, timestamp)
        update_db(timestamp, "complete")
    except Exception as e:
        print("ERROR: " + e)
        update_db(timestamp, "failed running reform")


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


def download(target_dir, URL):
    if URL:
        return wget.download(URL, target_dir)


def runReform(target_dir, ref_fasta, ref_gff, timestamp, position, chrom, in_fasta, in_gff, upstream_fasta,
              downstream_fasta):
    if position:
        command = 'python reform.py --chrom {} --position {} --in_fasta {} --in_gff {} --ref_fasta {} --ref_gff {} ' \
                  '--output_dir {}'.format(chrom,
                                           position,
                                           os.path.join(target_dir, secure_filename(in_fasta)),
                                           os.path.join(target_dir, secure_filename(in_gff)),
                                           ref_fasta,
                                           ref_gff,
                                           "./results/" + timestamp + "/"
                                           )
    else:
        command = 'python reform.py --chrom {} --upstream_fasta {} --downstream_fasta {} --in_fasta {} --in_gff {} ' \
                  '--ref_fasta {} --ref_gff {} --output_dir {}'.format(chrom,
                                                                       os.path.join(target_dir,
                                                                                    secure_filename(upstream_fasta)),
                                                                       os.path.join(target_dir,
                                                                                    secure_filename(downstream_fasta)),
                                                                       os.path.join(target_dir,
                                                                                    secure_filename(in_fasta)),
                                                                       os.path.join(target_dir,
                                                                                    secure_filename(in_gff)),
                                                                       ref_fasta,
                                                                       ref_gff,
                                                                       "./results/" + timestamp + "/"
                                                                       )
    os.system("mkdir results/" + timestamp)
    os.system(command)
    os.system('tar -czf results/' + timestamp + '/' + timestamp + '.tar.gz -C results/' + timestamp + '/ .')


def send_email(email, timestamp):
    with app.app_context():
        msg = Message('reform results', sender='reform-test@nyu.edu', recipients=[email])
        msg.html = "reform job complete. <a href='https://reform.bio.nyu.edu/download/" + timestamp \
                   + "'> Click here to download results.</a> "
        mail.send(msg)


def db_create():
    db = sqlite3.connect('database.db')
    db.execute(
        'CREATE TABLE submissions (timestamp TEXT, email TEXT, status TEXT, chrom TEXT, upstream_fasta TEXT, '
        'downstream_fasta TEXT, position TEXT, ref_fasta TEXT, ref_gff TEXT, in_fasta TEXT, in_gff TEXT)')
    db.close()


def update_db(timestamp, status):
    db = sqlite3.connect('database.db')
    db.execute("UPDATE submissions SET status=? where timestamp=? ", (status, timestamp))
    db.commit()
    db.close()
