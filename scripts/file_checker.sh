#!/usr/bin/env bash
# usage: script.sh -l url_file [-o output_file] [-h]
# NOTE: This is the fixed version — the original script you were given above is kept intact in the conversation.
set -uo pipefail   # <- removed -e so the script won't exit if wget returns non-zero

usage() {
cat <<'USAGE'
Usage: $(basename "$0") -l URL_FILE [-o OUTPUT_FILE] [-h]

Options:
  -l FILE    File containing URLs (one per line).  <--- REQUIRED
  -o FILE    Optional: save the entire terminal output (stdout+stderr) to FILE (appends).
  -h         Show this help message and exit.

Notes:
  - Lines that are empty or start with '#' in the URL file are skipped.
  - The script prints each URL in blue (ANSI) with one blank line before it,
    then runs: wget -t 2 --server-response --spider "URL".
  - Terminals do not support "half-line" spacing, so the script inserts a single blank line.
USAGE
}

# parse options
urlfile=""
outfile=""
while getopts ":l:o:h" opt; do
  case "$opt" in
    l) urlfile=$OPTARG ;;
    o) outfile=$OPTARG ;;
    h) usage; exit 0 ;;
    \?) echo "Error: invalid option -$OPTARG" >&2; usage; exit 2 ;;
    :)  echo "Error: option -$OPTARG requires an argument." >&2; usage; exit 2 ;;
  esac
done

# -l is compulsory
if [[ -z "${urlfile}" ]]; then
  echo "Error: -l URL file is required." >&2
  usage
  exit 2
fi

if [[ ! -f "$urlfile" ]]; then
  echo "Error: URL file '$urlfile' not found." >&2
  exit 2
fi

# If -o provided, route stdout+stderr through tee (append)
if [[ -n "${outfile}" ]]; then
  if ! touch "$outfile" 2>/dev/null; then
    echo "Error: cannot write to output file '$outfile'." >&2
    exit 2
  fi
  # redirect stdout+stderr through tee (append) but do NOT touch stdin
  exec > >(tee -- "$outfile") 2>&1
fi

# ANSI colors (works in most terminals)
BLUE=$'\033[34m'
RESET=$'\033[0m'

# ===== FIX: open the URL file on a dedicated FD (3) and read from fd 3
# This avoids any interaction between other redirections/process substitutions
# and the loop's stdin. It also prevents premature loop termination.
exec 3< "$urlfile" || { echo "Failed to open '$urlfile' for reading" >&2; exit 2; }

# process each URL (read from fd 3)
while IFS= read -r -u 3 url || [[ -n "$url" ]]; do
  # strip CR (for Windows-formatted files)
  url=${url%%$'\r'}
  # trim leading/trailing whitespace
  url="${url#"${url%%[![:space:]]*}"}"
  url="${url%"${url##*[![:space:]]}"}"

  # skip blanks and comments
  [ -z "$url" ] && continue
  [[ "$url" =~ ^# ]] && continue

  # print one blank line (terminals don't support half-line spacing)
  printf "\n"
  # print URL in blue
  printf "%b\n" "${BLUE}${url}${RESET}"

  # run wget (same options as your original script)
  # IMPORTANT: do not let a non-zero exit from wget stop the whole script
  # (the original script didn't exit on errors). Use "|| true" to continue on error.
  wget -t 2 -T 100 --server-response --spider "$url" || true

  # preserve the two blank lines after each run like original script
  printf "\n\n"
done

# close fd 3
exec 3<&-
