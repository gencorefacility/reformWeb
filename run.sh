#!/bin/bash

target_dir="$1"
timestamp="$2"
email="$3"
chrom="$4"
upstream_fasta="$5"
downstream_fasta="$6"
position="$7"
ref_fastaURL="$8"
ref_gffURL="$9"
in_fasta="${10}"
in_gff="${11}"

# Download files from user provided URLs to server
wget $ref_fastaURL -O $target_dir
ref_fasta=$(basename "$ref_fastaURL")
wget ref_gffURL -O $target_dir
ref_gff=$(basename "$ref_gffURL")

# Are the downloads compressed (gzip)
if [[ ${ref_fasta: -3} == ".gz" ]]; then
  gunzip $target_dir/$ref_fasta
  ref_fasta=${ref_fast0a:: -4}
fi

if [[ ${ref_gff: -3} == ".gz" ]]; then
  gunzip $target_dir/$ref_gff
  ref_gff=${ref_gff:: -4}
fi

# Run reform.py
mkdir -p ./results/$timestamp

if [ ! -z "$position" ]; then
  /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta $in_fasta \
  --in_gff $in_gff --ref_fasta $ref_fasta --ref_gff $ref_gff --output_dir "./results/$timestamp/"
else
  /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta $upstream_fasta \
  --downstream_fasta $downstream_fasta --in_fasta $in_fasta --in_gff $in_gff --ref_fasta $ref_fasta \
  --ref_gff $ref_gff --output_dir "./results/$timestamp/"
fi

tar -czf ./results/$timestamp/$timestamp.tar.gz -C results/$timestamp / .

