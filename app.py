import datetime

from flask import render_template, send_file, url_for
from markupsafe import Markup
from redis import Redis
from rq import Queue
from werkzeug.utils import redirect

from forms import SubmitJob, Testjob
from job import *

app = Flask(__name__)
# TODO: Move this secret_key out
app.secret_key = 'development key'

UPLOAD_FOLDER = './uploads'
# The type of file that needs to be uploaded to the server by user.
UPLOAD_FILES = ['in_fasta', 'in_gff']

# Route for submitting data on the production site.
@app.route('/', methods=['GET', 'POST'])
def submit():
    form = SubmitJob(request.form)
    # Validate user input according to the validation rules defined in forms.py.
    if request.method == 'POST' and form.validate():
        if (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename) and request.form[
            'position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit'))
        if (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename):
            if not (request.files['downstream_fasta'].filename and request.files['upstream_fasta'].filename):
                flash("Error: Must enter both upstream and downstream", 'error')
                return redirect(url_for('submit'))
        # Verify position is a number
        try:
            if request.form['position']:
                int(request.form['position'])
        except ValueError:
            flash("Error: Position must be an integer, like -1, 0, 1.", 'error')
            return redirect(url_for('submit'))
        # Verify that the name of the uploaded file is different
        if request.form['position'] and (request.files['in_fasta'].filename == request.files['in_gff'].filename):
            flash("Error: ref_fasta and ref_gff must be different files", 'error')
            return redirect(url_for('submit'))
        elif (request.files['downstream_fasta'].filename and request.files['upstream_fasta'].filename):
            filenames = [request.files['in_fasta'].filename, 
                request.files['in_gff'].filename, 
                request.files['downstream_fasta'].filename,
                request.files['upstream_fasta'].filename]
            if len(filenames) != len(set(filenames)):
                flash("Error: ref_fasta, ref_gff, downstream_fasta, upstream_fasta must be different files", 'error')
                return redirect(url_for('submit'))
        
        if not (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename) and not \
                request.form['position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit'))
        else:
            # User Submits Job #
            # (1) Create unique ID for each submission
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            target_dir = os.path.join(UPLOAD_FOLDER, timestamp)
            # (2) Log to Database
            if not os.path.isfile('database.db'):
                db_create()

            db_submit(request, timestamp)

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

            # (4) Send the job to the backend
            # Connect to the Redis server and intial a queue
            redis_conn = Redis() # This will connect to localhost:6379, db 0 by default

            # Determine the environment based on the REFORM_ENV environment variable
            reform_env = os.environ.get("REFORM_ENV")

            if reform_env == "development":
                queue_name = "dev_queue"
            elif reform_env == "production":
                queue_name = "prod_queue"
            else:
                # Fallback for safety, though it should ideally be set by Supervisor
                print(f"WARNING: REFORM_ENV not set or unknown value: {reform_env}. Defaulting to 'default' queue.")
                queue_name = "default"

            # Initialize the Queue with the determined queue_name
            q = Queue(queue_name, connection=redis_conn, default_timeout=3000)
            # Connect to the Redis server and intial a queue
            #redis_conn = Redis()
            #q = Queue(connection=redis_conn, default_timeout=3000)

            # Push job function and parameters into RQ
            job = q.enqueue(redisjob, args=(target_dir,
                                            timestamp,
                                            request.form['email'],
                                            request.form['chrom'],
                                            request.files['upstream_fasta'].filename,
                                            request.files['downstream_fasta'].filename,
                                            request.form['position'],
                                            request.form['ref_fasta'],
                                            request.form['ref_gff'],
                                            request.files['in_fasta'].filename,
                                            request.files['in_gff'].filename),
                            result_ttl=-1,
                            job_timeout=3000
                            )
            # (5) Update record in the database and flush message on the user front-end
            db_update(timestamp, "jobID", job.get_id())
            flash(Markup('JOB ID: ' + job.get_id() + '<br>' +
                         "You'll receive an e-mail when job is done with download link"), 'info')
    return render_template('form.html', form=form)

# Route for submitting data on the test site
@app.route('/test', methods=['GET', 'POST'])
def submit_test():

    # Path for local files
    DEFAULT_FILES = {
        'ref_fasta': './staticData/ref/test-ref.fa',
        'ref_gff': './staticData/ref/test-ref.gtf',
        'in_fasta': './staticData/inserted/test-in.fa',
        'in_gff': './staticData/inserted/test-in.gtf',
        'upstream_fasta': './staticData/up-down-seq/test-up.fa',
        'downstream_fasta': './staticData/up-down-seq/test-down.fa'
    }
    # Validate user input based on test site rule
    form = Testjob(request.form)
    if request.method == 'POST' and form.validate():
        if (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename) and request.form[
            'position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit_test'))
        if (request.files['downstream_fasta'].filename or request.files['upstream_fasta'].filename):
            if not (request.files['downstream_fasta'].filename and request.files['upstream_fasta'].filename):
                flash("Error: Must enter both upstream and downstream", 'error')
                return redirect(url_for('submit_test'))
        # Verify position is a number
        try:
            if request.form['position']:
                int(request.form['position'])
        except ValueError:
            flash("Error: Position must be an integer, like -1, 0, 1.", 'error')
            return redirect(url_for('submit_test'))
        # Verify that the name of the uploaded file is not empty and different
        if request.form['position'] and (request.files['in_fasta'].filename and request.files['in_gff'].filename) \
            and (request.files['in_fasta'].filename == request.files['in_gff'].filename):
            flash("Error: ref_fasta and ref_gff must be different files", 'error')
            return redirect(url_for('submit_test'))
        elif (request.files['downstream_fasta'].filename and request.files['upstream_fasta'].filename and request.files['in_fasta'].filename and request.files['in_gff'].filename):
            filenames_test = [request.files['in_fasta'].filename,
                request.files['in_gff'].filename,
                request.files['downstream_fasta'].filename,
                request.files['upstream_fasta'].filename]
            if len(filenames_test) != len(set(filenames_test)):
                flash("Error: ref_fasta, ref_gff, downstream_fasta, upstream_fasta must be different files", 'error')
                return redirect(url_for('submit_test'))
        else:
            # User Submits Job #
            # (1) Create unique ID for each submission
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            target_dir = os.path.join(UPLOAD_FOLDER, timestamp)
            # (2) Log to Database
            if not os.path.isfile('database.db'):
                db_create()


            # (3) Upload files from user device to server
            # Verify all files are present before uploading
            for files in UPLOAD_FILES:
                verified = verify_test_uploads(files)
                if not verified:
                    return redirect(url_for('submit_test'))

            # Choose to upload new files or use local files
            if verified:
                uploaded_files = {}
                for file_key in UPLOAD_FILES:
                    uploaded_files[file_key] = upload_test(target_dir, file_key, DEFAULT_FILES)
                # Set defualt None to up/down stream fasta
                for file_key in ['upstream_fasta', 'downstream_fasta']:
                    uploaded_files['upstream_fasta'] = None
                    uploaded_files['downstream_fasta'] = None
            
            # Uploaded upstream/downstream files when position is not provided
            if not request.form['position']:
                for file_key in ['upstream_fasta', 'downstream_fasta']:
                    uploaded_files[file_key] = upload_test(target_dir, file_key, DEFAULT_FILES)

            # Replace Ref Sequence with local path if test files detected
            if request.form['ref_fasta'] ==  'test-ref.fa':
                uploaded_files['ref_fasta'] = DEFAULT_FILES['ref_fasta']
            else:
                uploaded_files['ref_fasta'] = request.form['ref_fasta']
            if request.form['ref_gff'] ==  'test-ref.gtf':
                uploaded_files['ref_gff'] = DEFAULT_FILES['ref_gff']
            else:
                uploaded_files['ref_gff'] = request.form['ref_gff']
            
            db_test_submit(request, uploaded_files, timestamp)
            
            # (4) Send job to the backend
            # Use the redis queue as same as production site
            redis_conn = Redis() # This will connect to localhost:6379, db 0 by default

            # Determine the environment based on the REFORM_ENV environment variable
            reform_env = os.environ.get("REFORM_ENV")

            if reform_env == "development":
                queue_name = "dev_queue"
            elif reform_env == "production":
                queue_name = "prod_queue"
            else:
                # Fallback for safety, though it should ideally be set by Supervisor
                print(f"WARNING: REFORM_ENV not set or unknown value: {reform_env}. Defaulting to 'default' queue.")
                queue_name = "default"

            # Initialize the Queue with the determined queue_name
            q = Queue(queue_name, connection=redis_conn, default_timeout=3000)
            #redis_conn = Redis()
          
            #q = Queue(connection=redis_conn, default_timeout=3000)

            job = q.enqueue(redisjob, args=(target_dir,
                                            timestamp,
                                            request.form['email'], 
                                            request.form['chrom'], # 1
                                            uploaded_files['upstream_fasta'], # by default
                                            uploaded_files['downstream_fasta'],
                                            request.form['position'],
                                            uploaded_files['ref_fasta'], # by default
                                            uploaded_files['ref_gff'], # by default
                                            uploaded_files['in_fasta'], # by default
                                            uploaded_files['in_gff'] # by default
                                            ), 
                            result_ttl=-1,
                            job_timeout=3000
                            )
            # (5) Update record in the database and flush message on the user front-end
            db_update(timestamp, "jobID", job.get_id())
            flash(Markup('JOB ID: ' + job.get_id() + '<br>' +
                         "You'll receive an e-mail when job is done with download link"), 'info')
    return render_template('form.html', form=form)

# Route for downloading result
@app.route('/download/<timestamp>')
def downloadFile(timestamp):
    try:
        path = "./downloads/" + timestamp + "/reformed.tar.gz"
        return send_file(path, as_attachment=True)
    except:
        # flash(Markup('click <a href="./download/' + timestamp + '">here to download</a>'), 'info')
        flash("Download Error: File does not exist - " + path, 'error')
        return redirect(url_for('submit'))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
