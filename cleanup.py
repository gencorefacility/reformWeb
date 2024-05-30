import os
import logging
from datetime import datetime, timedelta

# Define the path for the log file
primary_log_directory = "/var/log/reform"

if not os.path.exists(primary_log_directory):
    local_log_dirs = "./cleanuplog" # If not, use the local log directory
    if not os.path.exists(local_log_dirs):
        os.makedirs(local_log_dirs)
    log_file_path = os.path.join(local_log_dirs, "cleanup.log")
else:
    log_file_path = os.path.join(primary_log_directory, "cleanup.log") # create cleanup.log in /var/log/reform

# Configure logging
logging.basicConfig(
    level=logging.INFO, # INFO, WARNING, ERROR, and CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

# Define the path to the downloads directory
download_folder = "./downloads"
# cutoff time = 72 hours ago
cutoff = datetime.now() - timedelta(hours=72)

# Traverse the download folder
# directory path, a list of sub-directories inside the current directory, and filenames
for root, dirs, files in os.walk(download_folder):
    for dir_name in dirs:
        dirpath = os.path.join(root, dir_name)
        # Get modification time
        dir_modified_time = datetime.fromtimestamp(os.path.getmtime(dirpath))
        # Check if the directory is older than 72 hours
        if dir_modified_time < cutoff:
            try:
                # Attempt to remove the directory
                os.rmdir(dirpath)
                logging.info(f"Removed old directory: {dirpath}") # log: remove folders
            except OSError as e:
                # If directory not empty, remove files inside first
                for root_dir, sub_dirs, sub_files in os.walk(dirpath, topdown=False):
                    for name in sub_files:
                        filepath = os.path.join(root_dir, name)
                        try:
                            os.remove(filepath)
                            logging.info(f"Removed file: {filepath}") # log: remove files
                        except Exception as e:
                            logging.error(f"Error removing file {filepath}: {e}")
                    for name in sub_dirs:
                        sub_dirpath = os.path.join(root_dir, name)
                        try:
                            os.rmdir(sub_dirpath)
                            logging.info(f"Removed directory: {sub_dirpath}")
                        except Exception as e:
                            logging.error(f"Error removing directory {sub_dirpath}: {e}")
                # Finally, remove the main directory
                try:
                    os.rmdir(dirpath)
                    logging.info(f"Removed old directory: {dirpath}")
                except Exception as e:
                    logging.error(f"Error removing directory {dirpath}: {e}")