#!/bin/bash

# Function to display help
display_help() {
    script_name="${0##*/}"
    echo ""
    echo "Usage: $script_name <anchor> <modifiable> [-h]"
    echo ""
    echo "Filters out domains from modifiable that are in anchor, removes duplicates, overwrites modifiable, then appends modifiable to anchor."
    echo ""
}

# Parse options
while getopts ":h" opt; do
    case $opt in
        h) display_help; exit 0 ;;
    esac
done

# Shift options
shift $((OPTIND - 1))

# Check if exactly two arguments are provided
if [ $# -ne 2 ]; then
    echo "Error: Both anchor and modifiable files must be specified."
    display_help
    exit 1
fi

anchor="$1"
modifiable="$2"

# Perform the operations
grep -vF -f "$anchor" "$modifiable" | sort -u > tmp && mv tmp "$modifiable"
cat "$modifiable" >> "$anchor"