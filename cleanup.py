import os
import logging
from datetime import datetime, timedelta

'''
This script is designed to manage and clean up old directories and files within the ./downloads folder.
Its primary purpose is to delete directories and their contents that are older than 72 hours to free up disk space
and maintain a clean file system. This script will iterate through all the files in the ./downloads folder
and delete all sub-folders and files if the folder was created more than 72 hours ago. If there are files in this folder,
the files will also be deleted one by one.
'''

# Configure logging
logging.basicConfig(
    level=logging.INFO, # INFO, WARNING, ERROR, and CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Define the path to the downloads directory
download_folder = "./downloads"
# cutoff time = 72 hours ago
cutoff = datetime.now() - timedelta(hours=72)

# Function to echo messages with timestamp
def echo_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.system(f"echo '{message} - {timestamp}'")


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
                echo_message(f"Removed old directory: {dirpath}") # echo: remove folders
            except OSError as e:
                # If directory not empty, remove files inside first
                for root_dir, sub_dirs, sub_files in os.walk(dirpath, topdown=False):
                    for name in sub_files:
                        filepath = os.path.join(root_dir, name)
                        try:
                            os.remove(filepath)
                            echo_message(f"Removed file: {filepath}") # echo: remove files
                        except Exception as e:
                            echo_message(f"Error removing file {filepath}: {e}")
                    for name in sub_dirs:
                        sub_dirpath = os.path.join(root_dir, name)
                        try:
                            os.rmdir(sub_dirpath)
                            echo_message(f"Removed directory: {sub_dirpath}")
                        except Exception as e:
                            echo_message(f"Error removing directory {sub_dirpath}: {e}")
                # Finally, remove the main directory
                try:
                    os.rmdir(dirpath)
                    echo_message(f"Removed old directory: {dirpath}")
                except Exception as e:
                    echo_message(f"Error removing directory {dirpath}: {e}")