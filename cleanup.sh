#!/bin/bash

# This script is designed to manage and clean up old directories and files within the ./downloads folder.
# Its primary purpose is to delete directories and their contents that are older than 1 week (168 hours) to free up disk space
# and maintain a clean file system. This script will iterate through all the files in the ./downloads folder
# and delete all sub-folders and files if the folder was created more than 1 week ago. If there are files in this folder,
# the files will also be deleted one by one.

# path to the downloads directory
download_folder="./downloads/"
# cutoffMins = 1 week ago = 168 hours ago (in seconds)
cutoffMins=$((168 * 60))

# Traverse the download folder and remove directories older than cutoff time
# -mindepth 1: Excludes the top-level directory, includes only subdirectories
find "$download_folder" -mindepth 1 -type d -mmin +$((cutoffMins)) | while read -r dirpath; do
    echo "$dirpath"
    if [ -d "$dirpath" ]; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        rm -rf "$dirpath"
        result=$? # capture successful or failure
        if [ $result -eq 0 ]; then
            echo "Removed old directory: $dirpath - $timestamp"
        else
            echo "Error removing directory: $dirpath - $timestamp"
        fi
    fi
done

