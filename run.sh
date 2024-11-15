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

# Function to determine if a path is a URL
is_url() {
    if [[ $1 =~ ^https?:// ]] || [[ $1 =~ ^ftp:// ]]; then
        return 0  # It's a URL
    else
        return 1  # It's a file path
    fi
}

# Function to process downloading and decompressing files
download_and_decompress() {
    local file_url=$1
    local target_path=$2
    local file_name=$(basename "$file_url")

    echo "Downloading $file_url"
    wget --no-check-certificate -nv "$file_url" -O "$target_path/$file_name"
    if [[ ${file_name: -3} == ".gz" ]]; then
        echo "pigz -d $target_path/$file_name"
        pigz -d "$target_path/$file_name"
        file_name=${file_name::-3} 
    fi
}

# Create the upload directories
echo "mkdir -p ./$target_dir"
mkdir -p "./$target_dir"

# Variables to hold the final paths to be used in the reform.py command
ref_fasta_path="$ref_fasta"
ref_gff_path="$ref_gff"

# Check and process the reference fasta file
if is_url "$ref_fasta"; then
    download_and_decompress "$ref_fasta" "./$target_dir"
    ref_fasta_path="./$target_dir/$(basename "$ref_fasta")"
    if [[ ${ref_fasta_path: -3} == ".gz" ]]; then
        ref_fasta_path="${ref_fasta_path::-3}"
    fi
else
    echo "Using local file: $ref_fasta"
    ref_fasta_path="$ref_fasta"
fi

# Check and process the reference gff file
if is_url "$ref_gff"; then
    download_and_decompress "$ref_gff" "./$target_dir"
    ref_gff_path="./$target_dir/$(basename "$ref_gff")"
    if [[ ${ref_gff_path: -3} == ".gz" ]]; then
        ref_gff_path="${ref_gff_path::-3}"
    fi
else
    echo "Using local file: $ref_gff"
    ref_gff_path="$ref_gff"
fi

# Validate all fasta files in uploads folder
uploads_dir="./uploads/$timestamp"
echo "Validating fasta files in $uploads_dir"
for fasta_file in "$uploads_dir"/*.fasta; do
    if [[ -f "$fasta_file" ]]; then
        echo "Validating $fasta_file"
        python3 ../fasta_validate.py "$fasta_file"
        if [[ $? -ne 0 ]]; then
            echo "Validation failed for $fasta_file"
            exit 1
        fi
    fi
done

# Run reform.py

if [ ! -z "$position" ]; then
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --position $position --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/" 2>&1 | tee ./results/$timestamp/$timestamp-worker-err.log
else
  echo   /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta ./uploads/$timestamp/$upstream_fasta \
  --downstream_fasta ./uploads/$timestamp/$downstream_fasta --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/"

  /home/reform/venv/bin/python reform.py --chrom $chrom --upstream_fasta ./uploads/$timestamp/$upstream_fasta \
  --downstream_fasta ./uploads/$timestamp/$downstream_fasta --in_fasta ./uploads/$timestamp/$in_fasta \
  --in_gff ./uploads/$timestamp/$in_gff --ref_fasta "$ref_fasta_path" --ref_gff "$ref_gff_path" \
  --output_dir "./results/$timestamp/" 2>&1 | tee ./results/$timestamp/$timestamp-worker-err.log
fi

# remove upload folder
echo "rm -Rf ./uploads/$timestamp"
rm -Rf ./uploads/$timestamp

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
