#!/usr/bin/env bash
set -u
# check_archived.sh - require -l listfile, optional -o outfile

usage() {
  cat <<EOF
Usage: $0 -l <listfile> [-o <outfile>]

-l <listfile>   File with one URL per line (required).
-o <outfile>    Save archived URLs to this file (optional).
EOF
  exit 2
}

listfile=""
outfile=""

while getopts ":l:o:" opt; do
  case "$opt" in
    l) listfile="$OPTARG" ;;
    o) outfile="$OPTARG" ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage ;;
    :) echo "Option -$OPTARG requires an argument." >&2; usage ;;
  esac
done

if [ -z "$listfile" ]; then
  echo "Missing -l <listfile>." >&2
  usage
fi

if [ ! -f "$listfile" ]; then
  echo "List file '$listfile' not found." >&2
  exit 3
fi

# If outfile was requested, write matches to a tempfile and move it on success.
tmp_out=""
if [ -n "$outfile" ]; then
  tmp_out="$(mktemp)" || { echo "Failed to create temp file." >&2; exit 4; }
  # ensure it's removed on exit if left behind
  trap 'rm -f "$tmp_out"' EXIT
fi

found_count=0

# Read file line-by-line; handle last line without newline and ignore blank/comment lines
while IFS= read -r url || [ -n "$url" ]; do
  # trim leading/trailing whitespace
  url="${url#"${url%%[![:space:]]*}"}"
  url="${url%"${url##*[![:space:]]}"}"

  # skip empty lines and lines starting with #
  [ -z "$url" ] && continue
  case "$url" in \#*) continue ;; esac

  # Query Wayback Availability API with proper URL encoding
  response="$(curl -sG --data-urlencode "url=$url" "https://archive.org/wayback/available")" || response=""

  # Check for available:true
  if printf '%s' "$response" | grep -q '"available":true'; then
    found_count=$((found_count + 1))
    if [ -n "$outfile" ]; then
      printf '%s\n' "$url" >> "$tmp_out"
    else
      printf '%s\n' "$url"
    fi
  fi
done < "$listfile"

if [ "$found_count" -eq 0 ]; then
  printf 'None of the URLs has been archived\n'
  # if outfile was requested, remove the temp file (so no empty file left)
  if [ -n "$outfile" ] && [ -f "$tmp_out" ]; then
    rm -f "$tmp_out"
    # clear trap so rm isn't attempted twice
    trap - EXIT
  fi
  exit 0
fi

# If we get here, there were matches and outfile may be requested
if [ -n "$outfile" ]; then
  # move temp to final destination (overwrite)
  mv -f "$tmp_out" "$outfile"
  trap - EXIT
  printf 'Saved %d archived URL(s) to %s\n' "$found_count" "$outfile"
fi

exit 0
