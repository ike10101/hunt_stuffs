#!/usr/bin/env bash

# Script to update multiple git repositories by adding, committing, and pushing changes.
# Usage: ./update_repos.sh ["commit message"]

# Default commit message
COMMIT_MESSAGE=${1:-"update"}

# List of directories to process
DIRS=(
  "/storage/emulated/0/Obsidian"
  "/storage/emulated/0/hunt_stuffs"
  "$HOME/subs_for_hunting"
  "$HOME/info_dis"
  "$HOME/targets"
)

for repo in "${DIRS[@]}"; do
  # Check if directory exists
  if [ -d "$repo" ]; then
    cd "$repo" || continue

    # Check if it's a git repository
    if [ -d ".git" ]; then
    echo -e "\n\n"
      echo -e "\033[0;34mBacking up $repo...\033[0m\n" 
      git add .
      git commit -m "$COMMIT_MESSAGE"
      git push
    fi
  fi
done
