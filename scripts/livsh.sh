#!/usr/bin/env bash
# A simple wrapper to run httpx on multiple files with include/exclude options
# Usage: ./httpx_wrapper.sh -i <file1 file2 ... | "*">
#        ./httpx_wrapper.sh -e <file_to_exclude1 ...>
#        ./httpx_wrapper.sh -h

# Function to display help message
show_help() {
  cat << EOF
Usage: $0 [-i <files>] | [-e <files>]

Options:
  -i    List of files to include (space-separated) or '*' for all files
  -e    List of files to exclude (space-separated); all others processed
  -h    Display this help message and exit

Examples:
  $0 -i file1 file2
  $0 -i "*"
  $0 -e exclude1 exclude2
EOF
}

# Parse flags
include_list=()
exclude_list=()
mode=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h)
      show_help; exit 0;
      ;;
    -i)
      mode="include"
      shift
      # collect all following args until next flag
      while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
        include_list+=("$1"); shift
      done
      ;;
    -e)
      mode="exclude"
      shift
      while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
        exclude_list+=("$1"); shift
      done
      ;;
    *)
      echo "Unknown option: $1"; show_help; exit 1;
      ;;
  esac
done

# Ensure exactly one of include or exclude is used
if [[ "$mode" != "include" && "$mode" != "exclude" ]]; then
  echo "Error: You must specify either -i or -e."; show_help; exit 1
fi

# Determine files to process
files=()
if [[ "$mode" == "include" ]]; then
  # If include is '*' literal, get all files in current dir
  if [[ ${#include_list[@]} -eq 1 && "${include_list[0]}" == "*" ]]; then
    for f in *; do files+=("$f"); done
  else
    files=("${include_list[@]}")
  fi
else
  # Exclude mode: start with all files, remove excluded
  for f in *; do
    skip=false
    for ex in "${exclude_list[@]}"; do
      [[ "$f" == "$ex" ]] && skip=true && break
    done
    $skip || files+=("$f")
  done
fi

# Get current directory name for output
dir_name="$(basename "$PWD")"
output_dir="$HOME/httpx_out_test/$dir_name"
mkdir -p "$output_dir"

# Loop through files and run httpx
for file in "${files[@]}"; do
  echo "Processing $file..."
  httpx -l "$file" -v -timeout 150 -t 100 -o "$output_dir/$file"  -retries 1 #-fc 5xx,4xx #-mc 200,201,401,403,400
  echo "$file" >> "$output_dir/$file"
  url_cleaner -i "$output_dir/$file"
done

echo "All tasks completed. Outputs in: $output_dir"