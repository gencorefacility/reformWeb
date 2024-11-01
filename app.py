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
UPLOAD_FILES = {'in_fasta': None, 'in_gff': None}

# Route for submitting data on the production site.
@app.route('/', methods=['GET', 'POST'])
def submit():
    form = SubmitJob(request.form)
    # Validate user input according to the validation rules defined in forms.py.
    if request.method == 'POST' and form.validate():
        # Get list of file names, and filter out empty files
        downstream_fasta_files = [file for file in request.files.getlist('downstream_fasta') if file.filename]
        upstream_fasta_files = [file for file in request.files.getlist('upstream_fasta') if file.filename]
        in_fasta_files = [file for file in request.files.getlist('in_fasta') if file.filename]
        in_gff_files = [file for file in request.files.getlist('in_gff') if file.filename]
        if (downstream_fasta_files or upstream_fasta_files) and request.form['position']:
            flash(f"Error: You must provide either the position, or the upstream and downstream sequences. Not all.", 'error')
            return redirect(url_for('submit'))
        if (downstream_fasta_files or upstream_fasta_files):
            if not (downstream_fasta_files and upstream_fasta_files):
                flash("Error: Must enter both upstream and downstream", 'error')
                return redirect(url_for('submit'))
        # Verify position is a number
        positions = None
        try:
            position_str = request.form['position']
            if position_str:
                positions = process_position(position_str)
                # print("Positions:", positions)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('submit'))
        # Verify that the name of the uploaded file is different by set()
        # User upload in_fasta and in_gff
        if in_fasta_files and in_gff_files:
            all_in_filenames = []
            in_fasta_filenames = [file.filename for file in in_fasta_files]
            in_gff_filenames = [file.filename for file in in_gff_files]
            all_in_filenames.extend(in_fasta_filenames)
            all_in_filenames.extend(in_gff_filenames)
            # When position provide
            if request.form['position'] and (len(all_in_filenames) != len(set(all_in_filenames))):
                flash("Error: in_fasta and in_gff must be different files", 'error')
                return redirect(url_for('submit'))
            # When position not provide, use upstream_fasta and downstream_fasta
            elif downstream_fasta_files and upstream_fasta_files:
                all_stream_fasta_filenames = []
                downstream_fasta_filenames = [file.filename for file in downstream_fasta_files]
                upstream_fasta_filenames = [file.filename for file in upstream_fasta_files]
                all_stream_fasta_filenames.extend(downstream_fasta_filenames)
                all_stream_fasta_filenames.extend(upstream_fasta_filenames)
                if len(all_stream_fasta_filenames) != len(set(all_stream_fasta_filenames)):
                    flash("Error: downstream_fasta, upstream_fasta must be different files", 'error')
                    return redirect(url_for('submit'))
                # Check all uniqueness for all files
                all_filenames = []
                all_filenames.extend(all_in_filenames)
                all_filenames.extend(all_stream_fasta_filenames)
                if len(all_filenames) != len(set(all_filenames)):
                    flash("Error: in_fasta, in_gff, downstream_fasta, upstream_fasta must be different files", 'error')
                    return redirect(url_for('submit'))
        if not (downstream_fasta_files or upstream_fasta_files) and not request.form['position']:
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
            for files in UPLOAD_FILES.keys():
                verified = verify_uploads(files)
                if not verified:
                    return redirect(url_for('submit'))

            # Upload Files to UPLOAD_DIR/timestamp/, and convert format to./uploads/$timestamp/item
            if verified:
                for key in UPLOAD_FILES.keys():
                    UPLOAD_FILES[key] = format_paths(upload(target_dir, key), target_dir)
                # Set defualt None to up/down stream fasta
                for file_key in ['upstream_fasta', 'downstream_fasta']:
                    UPLOAD_FILES[file_key] = None
                    UPLOAD_FILES[file_key] = None

            if not request.form['position']:
                UPLOAD_FILES['upstream_fasta'] = format_paths(upload(target_dir, 'upstream_fasta'), target_dir)
                UPLOAD_FILES['downstream_fasta'] = format_paths(upload(target_dir, 'downstream_fasta'), target_dir)

            # (4) Send the job to the backend
            # Connect to the Redis server and intial a queue
            redis_conn = Redis()
            q = Queue(connection=redis_conn, default_timeout=3000)

            # Push job function and parameters into RQ
            job = q.enqueue(redisjob, args=(target_dir,
                                            timestamp,
                                            request.form['email'],
                                            request.form['chrom'],
                                            UPLOAD_FILES['upstream_fasta'],
                                            UPLOAD_FILES['downstream_fasta'], #request.files['upstream_fasta'].filename,
                                            positions, #request.form['position'],
                                            request.form['ref_fasta'],
                                            request.form['ref_gff'],
                                            UPLOAD_FILES['in_fasta'],
                                            UPLOAD_FILES['in_gff']),
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
        downstream_fasta_files = [file for file in request.files.getlist('downstream_fasta') if file.filename]
        upstream_fasta_files = [file for file in request.files.getlist('upstream_fasta') if file.filename]
        in_fasta_files = [file for file in request.files.getlist('in_fasta') if file.filename]
        in_gff_files = [file for file in request.files.getlist('in_gff') if file.filename]
        if (downstream_fasta_files or upstream_fasta_files) and request.form['position']:
            flash("Error: You must provide either the position, or the upstream and downstream sequences.", 'error')
            return redirect(url_for('submit'))
        if (downstream_fasta_files or upstream_fasta_files):
            if not (downstream_fasta_files and upstream_fasta_files):
                flash("Error: Must enter both upstream and downstream", 'error')
                return redirect(url_for('submit'))
        # Verify position is a number
        positions = None
        try:
            position_str = request.form['position']
            if position_str:
                positions = process_position(position_str)
                # print("Positions:", positions)
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('submit'))
        # Verify that the name of the uploaded file is different when user upload (filename is not empty )
        # Verify that the name of the uploaded file is different by set()
        if in_fasta_files and in_gff_files:
            all_in_filenames = []
            in_fasta_filenames = [file.filename for file in in_fasta_files]
            in_gff_filenames = [file.filename for file in in_gff_files]
            all_in_filenames.extend(in_fasta_filenames)
            all_in_filenames.extend(in_gff_filenames)
            # When position provide
            if request.form['position'] and (len(all_in_filenames) != len(set(all_in_filenames))):
                flash("Error: in_fasta and in_gff must be different files", 'error')
                return redirect(url_for('submit'))
            # When position not provide, use upstream_fasta and downstream_fasta
            elif downstream_fasta_files and upstream_fasta_files:
                all_stream_fasta_filenames = []
                downstream_fasta_filenames = [file.filename for file in downstream_fasta_files]
                upstream_fasta_filenames = [file.filename for file in upstream_fasta_files]
                all_stream_fasta_filenames.extend(downstream_fasta_filenames)
                all_stream_fasta_filenames.extend(upstream_fasta_filenames)
                if len(all_stream_fasta_filenames) != len(set(all_stream_fasta_filenames)):
                    flash("Error: downstream_fasta, upstream_fasta must be different files", 'error')
                    return redirect(url_for('submit'))
                # Check all uniqueness for all files
                all_filenames = []
                all_filenames.extend(all_in_filenames)
                all_filenames.extend(all_stream_fasta_filenames)
                if len(all_filenames) != len(set(all_filenames)):
                    flash("Error: in_fasta, in_gff, downstream_fasta, upstream_fasta must be different files", 'error')
                    return redirect(url_for('submit'))
        if not (downstream_fasta_files or upstream_fasta_files) and not request.form['position']:
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

            # (3) Upload files from user device to server
            # Verify all files are present before uploading
            for files in UPLOAD_FILES:
                verified = verify_test_uploads(files)
                if not verified:
                    return redirect(url_for('submit_test'))

            # Choose to upload new files or use local files
            if verified:
                for file_key in UPLOAD_FILES.keys():
                    UPLOAD_FILES[file_key] = format_paths(upload_test(target_dir, file_key, DEFAULT_FILES), target_dir)
                # Set defualt None to up/down stream fasta
                for file_key in ['upstream_fasta', 'downstream_fasta']:
                    UPLOAD_FILES['upstream_fasta'] = None
                    UPLOAD_FILES['downstream_fasta'] = None
            
            # Uploaded upstream/downstream files when position is not provided
            if not request.form['position']:
                for file_key in ['upstream_fasta', 'downstream_fasta']:
                    UPLOAD_FILES[file_key] = format_paths(upload_test(target_dir, file_key, DEFAULT_FILES), target_dir)

            # Replace Ref Sequence with local path if test files detected
            if request.form['ref_fasta'] ==  'test-ref.fa':
                uploaded_files['ref_fasta'] = DEFAULT_FILES['ref_fasta']
            else:
                uploaded_files['ref_fasta'] = request.form['ref_fasta']
            if request.form['ref_gff'] ==  'test-ref.gtf':
                uploaded_files['ref_gff'] = DEFAULT_FILES['ref_gff']
            else:
                UPLOAD_FILES['ref_gff'] = request.form['ref_gff']
            
            db_test_submit(request, UPLOAD_FILES, timestamp)
            
            # (4) Send job to the backend
            # Use the redis queue as same as production site
            redis_conn = Redis()
          
            q = Queue(connection=redis_conn, default_timeout=3000)

            job = q.enqueue(redisjob, args=(target_dir,
                                            timestamp,
                                            request.form['email'], # ys4680@nyu.edu
                                            request.form['chrom'], # 1
                                            UPLOAD_FILES['upstream_fasta'], # by default
                                            UPLOAD_FILES['downstream_fasta'],
                                            positions,
                                            UPLOAD_FILES['ref_fasta'], # by default
                                            UPLOAD_FILES['ref_gff'], # by default
                                            UPLOAD_FILES['in_fasta'], # by default
                                            UPLOAD_FILES['in_gff'] # by default
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
