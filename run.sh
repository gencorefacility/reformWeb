#!/bin/bash

target_dir="$1"
timestamp="$2"
email="$3"
chrom="$4"
ref_fastaURL="$5"
ref_gffURL="$6"
in_fasta="$7"
in_gff="$8"

if [ "$#" -eq 9 ]; then
  position="$9"
elif [ "$#" -eq 10 ]; then
  upstream_fasta="$9"
  downstream_fasta="${10}"
fi

# Download files from user provided URLs to server
echo "wget ref_fasta"
ref_fasta=$(basename "$ref_fastaURL")
wget -nv $ref_fastaURL -O $target_dir/$ref_fasta

echo "wget ref_gff"
ref_gff=$(basename "$ref_gffURL")
wget -nv $ref_gffURL -O $target_dir/$ref_gff

# Are the downloads compressed (gzip)
if [[ ${ref_fasta: -3} == ".gz" ]]; then
  echo "gunzip $target_dir/$ref_fasta"
  gunzip $target_dir/$ref_fasta
  ref_fasta=${ref_fasta:: -3}
fi

if [[ ${ref_gff: -3} == ".gz" ]]; then
  echo "gunzip $target_dir/$ref_gff"
  gunzip $target_dir/$ref_gff
  ref_gff=${ref_gff:: -3}
fi

# Run reform.py
mkdir -p ./results/$timestamp

if [ ! -z "$position" ]; then
  echo /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"
else
  /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta ./uploads/$timestamp/$upstream_fasta \
  --downstream_fasta ./uploads/$timestamp/$downstream_fasta --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"
fi

#tar -czf ./results/$timestamp/$timestamp.tar.gz -C results/$timestamp / .

