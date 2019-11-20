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
ref_fasta=$(basename "$ref_fastaURL")
echo "wget -nv $ref_fastaURL -O $target_dir/$ref_fasta"
wget -nv $ref_fastaURL -O $target_dir/$ref_fasta

ref_gff=$(basename "$ref_gffURL")
echo "wget -nv $ref_gffURL -O $target_dir/$ref_gff"
wget -nv $ref_gffURL -O $target_dir/$ref_gff

# If downloads compresssed (gzip), uncompress with pigz
if [[ ${ref_fasta: -3} == ".gz" ]]; then
  echo "pigz -d $target_dir/$ref_fasta"
  pigz -d $target_dir/$ref_fasta
  ref_fasta=${ref_fasta:: -3}
fi

if [[ ${ref_gff: -3} == ".gz" ]]; then
  echo "pigz -d $target_dir/$ref_gff"
  pigz -d $target_dir/$ref_gff
  ref_gff=${ref_gff:: -3}
fi

# Run reform.py
echo "mkdir -p ./results/$timestamp"
mkdir -p ./results/$timestamp

if [ ! -z "$position" ]; then
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"
else
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta ./uploads/$timestamp/$upstream_fasta \
  --downstream_fasta ./uploads/$timestamp/$downstream_fasta --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta ./uploads/$timestamp/$upstream_fasta \
  --downstream_fasta ./uploads/$timestamp/$downstream_fasta --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta ./uploads/$timestamp/$ref_fasta --ref_gff ./uploads/$timestamp/$ref_gff \
  --output_dir "./results/$timestamp/"
fi

# remove upload folder
echo "rm -Rf ./uploads/$timestamp"
rm -Rf ./uploads/$timestamp

# create downloads directory
echo "mkdir -p ./downloads/$timestamp"
mkdir -p ./downloads/$timestamp

# compress reformed files to downloads
echo "tar cf - ./results/$timestamp/ | pigz --best > ./downloads/$timestamp/reformed.tar.gz"
tar cf - ./results/$timestamp/ | pigz --best > ./downloads/$timestamp/reformed.tar.gz
