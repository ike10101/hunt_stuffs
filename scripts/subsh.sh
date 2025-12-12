#!/usr/bin/env bash
# A simple wrapper script for subfinder with preset options.
# Usage: ./subfinder_wrapper.sh -dL <input_file> [-s <start_line>] [-e <end_line>] [-pc <provider_config>]
#        ./subfinder_wrapper.sh -h

# Default values
input_file=""
start_line=""
end_line=""

# Function to display help message
show_help() {
  echo "Usage: $0 -dL <input_file> [-s <start_line>] [-e <end_line>] [-pc <provider_config>]"
  echo
  echo "Options:" 
  echo "  -dL <input_file>     Path to the file containing domains to scan (required)"  
  echo "  -s <start_line>      Starting line number (1-based, optional)"  
  echo "  -e <end_line>        Ending line number (1-based, optional)"  
  echo "  -pc <provider_config> Provider config file (optional, overrides default)"
  echo "  -h                   Display this help message and exit"
  echo
  echo "Note: If -s and -e are equal, only that single line (domain) will be processed."
  echo "      Both -s and -e must be provided together if using a range."
}

# Parse arguments
if [[ $# -eq 0 ]]; then
  show_help
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h)
      show_help
      exit 0
      ;;
    -dL)
      # Capture the input file and shift past its argument
      input_file="$2"
      shift 2
      ;;
    -s)
      start_line="$2"
      shift 2
      ;;
    -e)
      end_line="$2"
      shift 2
      ;;
    -pc)
      pc="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Ensure input_file was provided
if [[ -z "$input_file" ]]; then
  echo "Error: -dL <input_file> is required."
  show_help
  exit 1
fi

# Check if input_file exists
if [[ ! -f "$input_file" ]]; then
  echo "Error: Input file '$input_file' does not exist."
  exit 1
fi

# Validate range if provided
if [[ -n "$start_line" || -n "$end_line" ]]; then
  if [[ -z "$start_line" || -z "$end_line" ]]; then
    echo "Error: Both -s and -e must be provided if using a range."
    show_help
    exit 1
  fi
  if ! [[ "$start_line" =~ ^[0-9]+$ && "$end_line" =~ ^[0-9]+$ ]]; then
    echo "Error: Start and end must be positive integers."
    exit 1
  fi
  if [[ "$start_line" -lt 1 || "$end_line" -lt 1 || "$start_line" -gt "$end_line" ]]; then
    echo "Error: Invalid range. Start and end must be >=1 with start <= end."
    exit 1
  fi
fi

# Determine directory name based on input_file (strip path and extension)
base_name="$(basename "$input_file")"
dir_name="${base_name%.*}"
output_dir="$HOME/vtx_targets/subdomains/$dir_name/"

# Create the output directory if it doesn't exist
mkdir -p "$output_dir"

# If range is specified, create temp file with extracted lines
temp_file=""
if [[ -n "$start_line" ]]; then
  temp_file=$(mktemp)
  sed -n "${start_line},${end_line}p" "$input_file" > "$temp_file"
  input_for_subfinder="$temp_file"
  trap 'rm -f "$temp_file"' EXIT
else
  input_for_subfinder="$input_file"
fi

# Run subfinder with the given file and preset options
subfinder -dL "$input_for_subfinder" -v -timeout 120 -oD "$output_dir" \
-rate-limit 1 -pc "$pc"

# Remove .txt extension from all files in the output directory
for file in "$output_dir"/*; do
  if [[ -f "$file" && "$file" == *.txt ]]; then
    mv "$file" "${file%.txt}"
  fi
done

echo "Subfinder scan completed. Results in: $output_dir"