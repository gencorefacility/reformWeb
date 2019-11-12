import datetime

from flask import Flask, render_template, send_file
from flask_mail import Mail
from redis import Redis
from rq import Queue

from forms import SubmitJob
from job import *

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

            redis_conn = Redis()
            q = Queue(connection=redis_conn)

            job = q.enqueue(redisjob, args=(target_dir,
                                            timestamp,
                                            request.form['email'],
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
            print(job.get_id())

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


if __name__ == '__main__':
    app.run(debug=True)
