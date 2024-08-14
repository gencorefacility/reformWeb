#!/bin/bash

# This script is designed to manage and clean up old directories and files within the ./downloads folder.
# Its primary purpose is to delete directories and their contents that are older than 1 week (168 hours) to free up disk space
# and maintain a clean file system. This script will iterate through all the folders in the /data/downloads folder
# and delete all sub-folders and files if the folder was created more than 1 week ago. 

# Define path to the downloads directory
download_folder="/data/downloads/"
cutoffDays=8

# Traverse the download folder and remove directories older than cutoff time
# -mindepth 1: Excludes the top-level directory, includes only subdirectories
find "$download_folder" -mindepth 1 -type d -ctime +${cutoffDays} -mtime +${cutoffDays} | while read -r dirpath; do
    # echo "$dirpath"
    rm -rfv "$dirpath"
done

