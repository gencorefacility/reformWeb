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

### Cannot SSH
SSH is only accessible on NYU VPN

