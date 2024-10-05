#!/bin/bash

target_dir="$1"
timestamp="$2"
email="$3"
chrom="$4"
ref_fasta="$5"
ref_gff="$6"
in_fasta="$7"
in_gff="$8"

if [ "$#" -eq 9 ]; then
  position="$9"
elif [ "$#" -eq 10 ]; then
  upstream_fasta="$9"
  downstream_fasta="${10}"
fi

echo "########################################"
echo "[$(date "+%D %T")] START $timestamp"
echo "########################################"

# create results folder
echo "mkdir -p ./results/$timestamp"
mkdir -p ./results/$timestamp

# redirect only stdout to the log file, keep stderr to worker.err.log and $timestamp-worker-err.log
log_file="./results/$timestamp/$timestamp-worker-out.log"
exec > >(tee -a "$log_file")

# Create the upload directories
echo "mkdir -p ./$target_dir"
mkdir -p "./$target_dir"

# Variables to hold the final paths to be used in the reform.py command
echo "Downloading $ref_fasta"
wget --no-check-certificate -nv "$ref_fasta" -O "$target_dir/$(basename "$ref_fasta")"
ref_fasta_path="$target_dir/$(basename "$ref_fasta")"

echo "Downloading $ref_gff"
wget --no-check-certificate -nv "$ref_gff" -O "$target_dir/$(basename "$ref_gff")"
ref_gff_path="$target_dir/$(basename "$ref_gff")"

# Run reform.py
# ./uploads/$timestamp/

if [ ! -z "$position" ]; then
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta $in_fasta \
  --in_gff $in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta $in_fasta \
  --in_gff $in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/" 2>&1 | tee ./results/$timestamp/$timestamp-worker-err.log
else
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta $upstream_fasta \
  --downstream_fasta $downstream_fasta --in_fasta $in_fasta \
  --in_gff $in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta $upstream_fasta \
  --downstream_fasta $downstream_fasta --in_fasta $in_fasta \
  --in_gff $in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/" 2>&1 | tee ./results/$timestamp/$timestamp-worker-err.log
fi

# # remove upload folder
# echo "rm -Rf ./uploads/$timestamp"
# rm -Rf ./uploads/$timestamp

# create downloads directory
echo "mkdir -p ./downloads/$timestamp"
mkdir -p ./downloads/$timestamp

# copy log files to download folder for email use
echo "cp -p ./results/$timestamp/$timestamp-worker-err.log ./results/$timestamp/$timestamp-worker-out.log ./downloads/$timestamp"
cp -p ./results/$timestamp/$timestamp-worker-err.log ./results/$timestamp/$timestamp-worker-out.log ./downloads/$timestamp

# compress reformed files and log files to downloads
echo "tar cf - ./results/$timestamp/ | pigz  > ./downloads/$timestamp/reformed.tar.gz"
tar cf - ./results/$timestamp/ | pigz > ./downloads/$timestamp/reformed.tar.gz

# remove results folder
echo "rm -Rf ./results/$timestamp"
rm -Rf ./results/$timestamp/

echo "########################################"
echo "[$(date "+%D %T")] END $timestamp"
echo "########################################"
