# *ref*ormWeb
A [*ref*orm](https://github.com/gencorefacility/reform) web UI implemented by [Flask](https://flask.palletsprojects.com/en/1.1.x/)

<p align="center">
  <img src="static/reform.png" width="20%">
</p>

## Installation
Installation script found at [`./INSTALL/install.sh`](https://github.com/gencorefacility/reformWeb/blob/master/INSTALL/install.sh)

## Using the Site

<p align="center">
<img src="https://gencore.bio.nyu.edu/wp-content/uploads/2018/10/the-solution.png" width="60%">
</p>

- Fill the form with the required parameters
  * `email` Email address to have notifications sent to
  * `chrom` ID of the chromsome to modify
  * `position` Position in chromosome at which to insert <in_fasta>. Can use -1 to add to end of chromosome. Note: Either position, or upstream AND downstream sequence must be provided.
  * `upstream_fasta` Path to Fasta file with upstream sequence. Note: Either position, or upstream AND downstream sequence must be provided.
  * `downstream_fasta` Path to Fasta file with downstream sequence. Note: Either position, or upstream AND downstream sequence must be provided.
  * `in_fasta` Path to new sequence to be inserted into reference genome in FASTA format.
  * `in_gff` Path to GFF file describing new fasta sequence to be inserted.
  * `ref_fasta` Path to reference fasta file.
  * `ref_gff` Path to reference gff file.
- After submission, the data and files will be gathered and submitted to a message queue to run [*ref*orm](https://github.com/gencorefacility/reform)
- If sucessful or failure, an e-mail will be sent to the e-mail address provided

## Using the Test Site
Test site is designed to help developers and researchers test updates more easily and quickly by using local files and default populated addresses. Files used for testing need to be uploaded in advance according to the requirements in INSTALL/install.sh.

- Fill the form with the required parameters
  * `email` Use the default test email address.
  * `chrom` Default is 1.
  * `position` User-provided.
  * `upstream_fasta`  If no file is uploaded, use the local upstream_fasta file.
  * `downstream_fasta` If no file is uploaded, use the local downstream_fasta file.
  * `in_fasta` If no file is uploaded, use the local in_fasta file.
  * `in_gff` If no file is uploaded, use the local in_gff file.
  * `ref_fasta` Use the example FTP link or the local ref_fasta file.
  * `ref_gff` Use the example FTP link or the local ref_gff file.

## Troubleshooting

### Error or Unexepected behavior when submitting form
Check the logic here in `app.py`
https://github.com/gencorefacility/reformWeb/blob/a6b7e7530c8508bf3ee80c57690e314432541e13/app.py#L24-L37

### No Activity or Emails
Check that reform (gunicorn) and rq workers services running with `supervisorctl`.
```bash
[root@reform ~]# supervisorctl status
reform                           STOPPED   Feb 15 10:36 AM
worker                           STOPPED   Feb 15 10:36 AM
```
Start or restart if needed
```bash
[root@reform ~]# supervisorctl start all
worker: started
reform: started
```

### How to monitor logs
Logs are written to `/var/log/reform`. Most of the echo outs are controlled in `run.sh`. Edit as needed for debugging.
* `reform.err.log` Contains errors from Flask (e.g., errors in app.py) and ERROR, INFO logs from Gunicorn.
* `reform.out.log` Contains standard output from Gunicorn.
* `worker.out.log` Contains echo outputs from run.sh, indicating the current task of the worker.
* `worker.err.log` Contains errors from reform.py and FTP download records.

### Receive an Email with a Zip of an Empty Download Folder
An empty download folder means `reform` didn't finish, resulting in empty `result` and `download` folders. To debug this error, please check `/var/log/reform` for more information. Here are some common issues:

**In `worker.err.log`:**

1. **`OSError: [Errno 28] No space left on device`**:
   - There is no free space on the server. Please clean up files in `/data/downloads/`, `/data/results/`, and `/data/uploads/`.
2. **`FileNotFoundError: [Errno 2] No such file or directory`**:
   - Please check the corresponding folder, especially when using the test site.

**In `worker.err.log`:**

1. **`./run.sh: line XX: syntax error near unexpected token`**:
   - An invalid input has been passed into `run.sh`, usually an invalid FTP link.

### Get Error Status Code when access reform web
Error status code usually represent the web service has not run as expectly.
1. `502 Bad Gateway`: This error typically occurs due to communication problems between servers. It might be helpful to check `app.py` for any unhandled routes.
2. `500 Internal Server Error`: This error indicates that the server encountered an unexpected condition that prevented it from fulfilling the request. Check `/var/log/reform/reform.err.log` for detailed information.

### Cannot SSH
SSH is only accessible on NYU VPN

