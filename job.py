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
    python_exec_path = os.path.expanduser("~/venv/bin/python")

    if position:
        command_list = ["bash", "./run.sh", python_exec_path, target_dir, timestamp, email, chrom,
                        ref_fastaURL, ref_gffURL, in_fasta, in_gff, position]
    else:
        command_list = ["bash", "./run.sh", python_exec_path, target_dir, timestamp, email, chrom,
                        ref_fastaURL, ref_gffURL, in_fasta, in_gff, upstream_fasta, downstream_fasta]

    status=1
    try:
        # Using subprocess.run with check=True to raise an exception on non-zero exit codes
        # You might want to capture stdout/stderr for debugging:
        result = subprocess.run(command_list, check=True, capture_output=True, text=True)
        print("Command output:", result.stdout)
        print("Command error:", result.stderr)
        #subprocess.run(command_list, check=True) # This will raise CalledProcessError if run.sh fails

#        os.system("echo Emailing") # Consider replacing os.system with subprocess.run here too
 #       send_email(email, timestamp)
 #       os.system("echo Emailed")
        status=0
        db_update(timestamp, "status", "complete")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"Error executing command: {e}") # Print the error for debugging
        db_update(timestamp, "status", "failed")
    except Exception as e: # Catch other potential exceptions during execution
        os.system("echo An unexpected error occurred")
        print(f"Unexpected error: {e}")
        db_update(timestamp, "status", "failed")

    os.system("echo Emailing") # Consider replacing os.system with subprocess.run here too
    send_email(email, timestamp, status)
    os.system("echo Emailed")

# Determine if this file is accepted by checking the file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Verify that the file is uploaded to the form and it is allowed
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

# verify_uploads() for test site
def verify_test_uploads(file):
    fileObj = request.files[file]
    # Not require user to upload files
    if fileObj.filename == '':
        # flash('No ' + file + ' file selected for uploading', 'error')
        # return False
        return True # If no file is uploaded then the default file is used
    if fileObj and allowed_file(fileObj.filename):
        return True
    else:
        flash('Invalid File Type for ' + file, 'error')
        return False


# Upload files to uploads/timestamp 
def upload(target_dir, file):
    fileObj = request.files[file]
    # make the directory based on timestamp
    os.system('mkdir -p ' + target_dir)
    # save the file
    fileObj.save(os.path.join(target_dir,
                              secure_filename(fileObj.filename)))

# upload file function for test site, return by filename
def upload_test(target_dir, file_key, default_files):
    # if file is empty (indicated use default file), fileObj set to None
    fileObj = request.files[file_key] if file_key in request.files else None
    os.makedirs(target_dir, exist_ok=True) # dirs for upload files
    
    # User provided new files in form
    if fileObj:
        # save the uploaded file
        filename = secure_filename(fileObj.filename)
        file_path = os.path.join(target_dir, filename)
        fileObj.save(file_path)
        return fileObj.filename
    else:
        # Use default file if no file was uploaded
        src = os.path.abspath(default_files[file_key])
        dst = os.path.join(target_dir, os.path.basename(src))
        # Create soft link in uploads/timestamp
        if not os.path.exists(dst):
            os.symlink(src, dst)
        return os.path.basename(src)


def download(target_dir, URL):
    if URL:
        return wget.download(URL, target_dir)

def send_email(email, timestamp, status):
    # Set DDL to 1 week later (168hrs) - only relevant for success email
    deadline = datetime.now() + timedelta(hours=168)
    deadline_str = deadline.strftime('%B %d, %Y')

    err_log_path = f"./downloads/{timestamp}/{timestamp}-worker-err.log"
    out_log_path = f"./results/{timestamp}/{timestamp}-worker-out.log" # Assuming a worker-out.log is also generated

    err_log_content = "No error log content available."
    out_log_content = "No output log content available."

    # Read the content of the log files (safely)
    if os.path.exists(err_log_path):
        try:
            with open(err_log_path, 'r') as file:
                err_log_content = file.read()
        except Exception as e:
            err_log_content = f"Could not read error log file: {e}"
    else:
        err_log_content = f"Error log file not found at: {err_log_path}"


    if os.path.exists(out_log_path):
        try:
            with open(out_log_path, 'r') as file:
                out_log_content = file.read()
        except Exception as e:
            out_log_content = f"Could not read output log file: {e}"
    else:
        out_log_content = f"Output log file not found at: {out_log_path}"


    with j.app_context(): # Ensure this context is available where send_email is called
        if status == 0:
            # Success Email
            subject = f"Reform Results - Download Deadline: {deadline_str}"
            msg = Message(subject, sender='reform@nyu.edu', recipients=[email])
            msg.html = f"""<i>ref</i>orm job complete.
                            <a href='https://reform.bio.nyu.edu/download/{timestamp}'>Click here to download results</a>.
                            The file will be available for the next 7 days until {deadline_str}.<br><br>

                            If you use <i>ref</i>orm in your research, please cite the GitHub repository:<br>
                            https://github.com/gencorefacility/reform<br><br>

                            <b>Reform Output:</b><br><pre>{err_log_content}</pre><br>
                            """
        else:
            # Error Email
            subject = 'Reform Results - ERROR'
            msg = Message(subject, sender='reform@nyu.edu', recipients=[email])
            msg.html = f"""<i>ref</i>orm job had an error. Please review and resubmit. <br><br>
                            <b>Output:</b><br><pre>{out_log_content}</pre>
                            """
        try:
            j.extensions['mail'].send(msg) # Correct way to access Flask-Mail instance
            print(f"Email sent successfully for job {timestamp} (Status: {status}) to {email}")
        except Exception as mail_e:
            print(f"Failed to send email for job {timestamp} (Status: {status}) to {email}: {mail_e}")


    # Remove the log files - this should happen regardless of email status
    # Be careful with os.remove if the files are critical for debugging or auditing.
    # It might be better to move them to an archive folder or clean up later.
    if os.path.exists(err_log_path):
        try:
            os.remove(err_log_path)
            print(f"Removed {err_log_path}")
        except Exception as e:
            print(f"Error removing {err_log_path}: {e}")

    if os.path.exists(out_log_path):
        try:
            os.remove(out_log_path)
            print(f"Removed {out_log_path}")
        except Exception as e:
            print(f"Error removing {out_log_path}: {e}")

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
