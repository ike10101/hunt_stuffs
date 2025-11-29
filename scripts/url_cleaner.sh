#!/bin/sh

# Check for help flag
if [ "$1" = "-h" ]; then
    echo "Usage: script [-h] [-i file | -d dir]"
    exit 0
fi

# Check if the first argument is '-i' for a single input file
if [ "$1" = "-i" ]; then
    if [ -z "$2" ]; then
        echo "Error: -i requires a file argument"
        exit 1
    fi
    input_file="$2"
    if [ ! -f "$input_file" ]; then
        echo "Error: File '$input_file' does not exist"
        exit 1
    fi
    # Process the file and overwrite it using a temporary file
    temp_file=$(mktemp)
    sed 's#^https\?://\(www\.\)\?##' "$input_file" | sort -u > "$temp_file"
    mv "$temp_file" "$input_file"

# Check if the first argument is '-d' for a directory
elif [ "$1" = "-d" ]; then
    if [ -z "$2" ]; then
        echo "Error: -d requires a directory argument"
        exit 1
    fi
    dir="$2"
    if [ ! -d "$dir" ]; then
        echo "Error: Directory '$dir' does not exist"
        exit 1
    fi
    # Process each file in the directory
    for file in "$dir"/*; do
        if [ -f "$file" ]; then
            temp_file=$(mktemp)
            sed 's#^https\?://\(www\.\)\?##' "$file" | sort -u > "$temp_file"
            mv "$temp_file" "$file"
        fi
    done

# Invalid usage
else
    echo "Usage: script [-h] [-i file | -d dir]"
    exit 1
fi
