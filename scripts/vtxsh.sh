#!/usr/bin/env bash
# vtx_wrapper.sh: run vtx against multiple files with include/exclude options,
# then uniq-sort each output file in-place.
#
# Usage:
#   ./vtx_wrapper.sh -i <file1 file2 ... | "*">
#   ./vtx_wrapper.sh -e <file_to_exclude1 ...>
#   ./vtx_wrapper.sh -h
#
# Note: this script expects your API keys or credentials in the environment
# variable $keys. E.g. export keys="myapikey" before running.

set -euo pipefail

show_help() {
  cat << EOF
Usage: $0 [-i <files>] | [-e <files>]

Options:
  -i    List of files to include (space-separated), or "*" for all files
  -e    List of files to exclude (space-separated); all others processed
  -h    Show this help message and exit

Examples:
  $0 -i domains1.txt domains2.txt
  $0 -i "*"
  $0 -e skip_this.txt skip_that.txt

Ensure you have exported your credentials:
  export keys="YOUR_API_KEYS"
EOF
}

# --- Parse flags ---
include_list=()
exclude_list=()
mode=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h)
      show_help
      exit 0
      ;;
    -i)
      mode="include"
      shift
      while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
        include_list+=( "$1" )
        shift
      done
      ;;
    -e)
      mode="exclude"
      shift
      while [[ $# -gt 0 && ! "$1" =~ ^- ]]; do
        exclude_list+=( "$1" )
        shift
      done
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

if [[ "$mode" != "include" && "$mode" != "exclude" ]]; then
  echo "Error: you must specify exactly one of -i or -e."
  show_help
  exit 1
fi

# --- Build list of files to process ---
files=()
if [[ "$mode" == "include" ]]; then
  # if literal "*", include every file in cwd
  if [[ "${#include_list[@]}" -eq 1 && "${include_list[0]}" == "*" ]]; then
    for f in *; do files+=( "$f" ); done
  else
    files=( "${include_list[@]}" )
  fi
else
  # exclude mode: start with all, drop those in exclude_list
  for f in *; do
    skip=false
    for ex in "${exclude_list[@]}"; do
      [[ "$f" == "$ex" ]] && skip=true && break
    done
    $skip || files+=( "$f" )
  done
fi

# --- Prepare output directory ---
cwd_name="$(basename "$PWD")"
output_dir="$HOME/vtx_urls/$cwd_name"
log_dir="$HOME/vtx_urls/logs/$cwd_name"
mkdir -p "$output_dir"
mkdir -p "$log_dir"

# --- Run vtx on each file ---
for file in "${files[@]}"; do
  echo ">>> Running vtx on '$file'..."
  python /storage/emulated/0/vtx_hunt/scripts/vtx.py -l "$file" -k "$keys" --all -v \
      -o "$output_dir/$file" -timeout 90 -log "$log_dir/$file"
done

echo "Done! Results are in: $output_dir/"
