import os
import sqlite3
import subprocess

import wget
from flask import request, flash, Flask
from flask_mail import Message, Mail
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

from forms import ALLOWED_EXTENSIONS

j = Flask(__name__)

j.config['MAIL_SERVER'] = 'smtp.nyu.edu'
j.config['MAIL_PORT'] = 25
j.config['MAIL_USERNAME'] = 'reform-test@nyu.edu'
j.config['MAIL_PASSWORD'] = ''
j.config['MAIL_USE_TLS'] = False
j.config['MAIL_USE_SSL'] = False
mail = Mail(j)


def redisjob(target_dir, timestamp, email, chrom, upstream_fasta, downstream_fasta, position, ref_fastaURL, ref_gffURL,
             in_fasta, in_gff):
    # Convert list of insert sequences to string
    in_fasta_str  = ','.join(in_fasta)
    in_gff_str = ','.join(in_gff)
    if position:

        command = "bash ./run.sh {} {} {} {} {} {} {} {} {}".format(target_dir, timestamp, email, chrom,
                                                                    ref_fastaURL, ref_gffURL, in_fasta_str,
                                                                    in_gff_str, position)
    else:
        upstream_fasta_str  = ','.join(upstream_fasta)
        downstream_fasta_str  = ','.join(downstream_fasta)
        command = "bash ./run.sh {} {} {} {} {} {} {} {} {} {}".format(target_dir, timestamp, email, chrom,
                                                                       ref_fastaURL, ref_gffURL, in_fasta_str,
                                                                       in_gff_str, upstream_fasta_str,
                                                                       downstream_fasta_str)
    try:
        #subprocess.run([command])
        os.system(command)
        os.system("echo Emailing")
        send_email(email, timestamp)
        os.system("echo Emailed")
        db_update(timestamp, "status", "complete")
    except:
        os.system("echo Command Failed")
        send_email_error(email)




def redisjob1(target_dir, timestamp, email, chrom, upstream_fasta, downstream_fasta, position, ref_fastaURL, ref_gffURL,
              in_fasta, in_gff):
    # (4) Download files from user provided URLs to server
    try:
        ref_fasta = download(target_dir, ref_fastaURL)
        ref_gff = download(target_dir, ref_gffURL)
    except:
        # TODO: e-mal of failure
        print("ERROR: ")
        db_update(timestamp, "status", "failed to download references")

    # Are the downloads compressed (gzip)
    if "gz" in ref_fasta:
        os.system("gunzip " + ref_fasta)
        ref_fasta = ref_fasta[0:-3]
    if "gz" in ref_gff:
        os.system("gunzip " + ref_gff)
        ref_gff = ref_gff[0:-3]

    # (5) Run the reform.py
    try:
        runReform(target_dir, ref_fasta, ref_gff, timestamp, position, chrom, in_fasta, in_gff, upstream_fasta,
                  downstream_fasta)
        send_email(email, timestamp)
        db_update(timestamp, "status", "complete")
    except:
        print("ERROR: ")
        db_update(timestamp, "status", "failed running reform")

# Determine if this file is accepted by checking the file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Verify that the file is uploaded to the form and it is allowed
def verify_uploads(file):
    fileObj_lists = request.files.getlist(file)
    for uploaded_file in fileObj_lists:
        if uploaded_file.filename == '':
            flash('No ' + file + ' file selected for uploading', 'error')
            return False
        if uploaded_file and allowed_file(uploaded_file.filename):
            continue
        else:
            flash('Invalid File Type for ' + file, 'error')
            return False
    return True

# verify_uploads() for test site
def verify_test_uploads(file):
    fileObj_lists = request.files.getlist(file)
    for uploaded_file in fileObj_lists:
        # Not require user to upload files
        if uploaded_file.filename == '':
            # flash('No ' + file + ' file selected for uploading', 'error')
            # return False
            continue # If no file is uploaded then the default file is used
        if uploaded_file and allowed_file(uploaded_file.filename):
            continue
        else:
            flash('Invalid File Type for ' + file, 'error')
            return False
    return True


# Upload files to uploads/timestamp 
def upload(target_dir, file):
    fileObj_lists = request.files.getlist(file)
    # make the directory based on timestamp
    os.system('mkdir -p ' + target_dir)
    # save the file
    filenames = []
    for fileObj in fileObj_lists:
        filename = secure_filename(fileObj.filename)
        fileObj.save(os.path.join(target_dir, filename))
        filenames.append(filename)
    return filenames

# upload file function for test site, return by filename
def upload_test(target_dir, file_key, default_files):
    # if file is empty (indicated use default file), fileObj set to None
    fileObj_lists = request.files.getlist(file_key) if file_key in request.files else []
    os.makedirs(target_dir, exist_ok=True) # dirs for upload files
    
    # User provided new files in form
    filenames = []
    if fileObj_lists:
        for fileObj in fileObj_lists:
            # save the uploaded file
            filename = secure_filename(fileObj.filename)
            file_path = os.path.join(target_dir, filename)
            fileObj.save(file_path)
            filenames.append(fileObj.filename)
    else:
        # default_files is a list of file names
        src_files = default_files[file_key]
        for src in src_files:
            # Use default file if no file was uploaded
            src = os.path.abspath(default_files[file_key])
            dst = os.path.join(target_dir, os.path.basename(src))
            # Create soft link in uploads/timestamp
            if not os.path.exists(dst):
                os.symlink(src, dst)
            filenames.append(os.path.basename(src))
    return filenames


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
    os.system("mkdir -p results/" + timestamp)
    os.system(command)
    os.system('tar -czf results/' + timestamp + '/' + timestamp + '.tar.gz -C results/' + timestamp + '/ .')


def send_email(email, timestamp):
    # Set DDL to 1 week later (168hrs)
    deadline = datetime.now() + timedelta(hours=168)
    deadline_str = deadline.strftime('%B %d, %Y')

    # paths to the log files
    err_log_path = f"./downloads/{timestamp}/{timestamp}-worker-err.log"
    out_log_path = f"./downloads/{timestamp}/{timestamp}-worker-out.log"

    # read the content of the log files
    with open(err_log_path, 'r') as file:
        err_log_content = file.read()

    with open(out_log_path, 'r') as file:
        out_log_content = file.read()

    with j.app_context():
        subject = f"Reform Results - Download Deadline: {deadline_str}"
        msg = Message(subject, sender='reform@nyu.edu', recipients=[email])
        msg.html = f"""Reform job complete. 
                    <a href='https://reform.bio.nyu.edu/download/{timestamp}'>Click here to download results</a>. 
                    The file will be available for the next 7 days until {deadline_str}. If you do not download the file before this time, it will be deleted. <br><br>

                    If you use reform in your research, please cite the GitHub repository:<br>
                    reform: https://github.com/gencorefacility/reform<br><br>
                    
                    You may also cite our article:<br>
                    Mohammed Khalfan, Eric Borenstein, Pieter Spealman, Farah Abdul-Rahman, and David Gresham (2021).<br>
                    <i>Modifying Reference Sequence and Annotation Files Quickly and Reproducibly with reform.</i><br>
                    
                    <b>Reform.py Output Log:</b><br><pre>{err_log_content}</pre><br>
                    <b>Worker Output Log:</b><br><pre>{out_log_content}</pre>
                    """
        mail.send(msg)

    # Remove the log files from the download folder
    os.remove(err_log_path)
    os.remove(out_log_path)


def send_email_error(email):
    with j.app_context():
        msg = Message('reform results - error', sender='reform@nyu.edu', recipients=[email])
        msg.html = "reform job had an error. Please resubmit."
        mail.send(msg)


def db_create():
    db = sqlite3.connect('database.db')
    db.execute(
        'CREATE TABLE submissions (jobID TEXT, timestamp TEXT, email TEXT, status TEXT, chrom TEXT, upstream_fasta '
        'TEXT, downstream_fasta TEXT, position TEXT, ref_fasta TEXT, ref_gff TEXT, in_fasta TEXT, in_gff TEXT)')
    db.close()


def db_submit(request, timestamp):
    try:
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO submissions (jobID, timestamp, email, status, chrom, upstream_fasta, '
                'downstream_fasta, position, ref_fasta, ref_gff, in_fasta, in_gff ) VALUES(?, ?, ?, ?, ?, ?, '
                '?, ?, ?, ?, ?, ?)',
                ("none",
                 timestamp,
                 request.form['email'],
                 "submitted",
                 request.form['chrom'],
                 request.files['upstream_fasta'].filename,
                 request.files['downstream_fasta'].filename,
                 request.form['position'],
                 request.form['ref_fasta'],
                 request.form['ref_gff'],
                 request.files['in_fasta'].filename,
                 request.files['in_gff'].filename)
            )
            con.commit()
    except:
        con.rollback()
        flash("error in insert operation ", 'error')

def db_test_submit(request, uploaded_files, timestamp):
    try:
        with sqlite3.connect("database.db") as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO submissions (jobID, timestamp, email, status, chrom, upstream_fasta, '
                'downstream_fasta, position, ref_fasta, ref_gff, in_fasta, in_gff ) VALUES(?, ?, ?, ?, ?, ?, '
                '?, ?, ?, ?, ?, ?)',
                ("none",
                 timestamp,
                 request.form['email'],
                 "submitted",
                 request.form['chrom'],
                 uploaded_files['upstream_fasta'],
                 uploaded_files['downstream_fasta'],
                 request.form['position'],
                 uploaded_files['ref_fasta'],
                 uploaded_files['ref_gff'],
                 uploaded_files['in_fasta'],
                 uploaded_files['in_gff'])
            )
            con.commit()
    except:
        con.rollback()
        flash("error in insert operation ", 'error')


def db_update(timestamp, set_id, set_value):
    db = sqlite3.connect('database.db')
    db.execute("UPDATE submissions SET " + set_id + "=? where timestamp=? ", (set_value, timestamp))
    db.commit()
    db.close()

def process_position(position_str):
    try:
        position = int(position_str)
        return position_str  # return Str
    except ValueError:
        try:
            position_list = [pos.strip() for pos in position_str.split(',')]
            for pos in position_list:
                int(pos)
            return position_str
        except ValueError:
            raise ValueError("Position must be an integer or a comma-separated list of integers.")

# Format file path into: ./uploads/$timestamp/item
def format_paths(file_list, target_dir):
            return [os.path.join(target_dir, filename) for filename in file_list]

# Checks if any file in the list is empty.
def check_files_not_empty(file_list):
    for file in file_list:
        if file.content_length == 0:
            flash(f"Error: {file.filename} is empty, please upload a valid file.", 'error')
            return False
    return True