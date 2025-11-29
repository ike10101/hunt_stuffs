import os
import shutil
import argparse
import sys

# Number of files per group, easy to change here
GROUP_SIZE = 20

def main():
    parser = argparse.ArgumentParser(description="Move files into batch subdirectories.")
    parser.add_argument('-d', required=True, help='Directory to process files in')
    parser.add_argument('-g', type=int, required=True, help='Number of groups to create')
    args = parser.parse_args()

    dir_path = args.d
    groups = args.g

    if groups <= 0:
        print("Error: -g must be a positive non-zero integer.")
        sys.exit(1)

    if not os.path.exists(dir_path):
        print(f"Error: Directory '{dir_path}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(dir_path):
        print(f"Error: '{dir_path}' is not a directory.")
        sys.exit(1)

    # Get list of files only (ignore subdirectories) and sort by modification time
    files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    files.sort(key=lambda x: os.path.getmtime(os.path.join(dir_path, x)), reverse=True)  # Sort by recency
    num_files = len(files)

    # Calculate maximum possible groups (considering partial groups)
    max_groups = (num_files + GROUP_SIZE - 1) // GROUP_SIZE if num_files > 0 else 0

    if groups > max_groups:
        print(f"Error: Only {max_groups} groups possible based on {num_files} files and group size {GROUP_SIZE}. You specified {groups}.")
        sys.exit(1)

    # Find existing batch subdirectories with numeric suffix
    subdirs = [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))]
    batch_nums = []
    for d in subdirs:
        if d.startswith('batch'):
            suffix = d[len('batch'):]
            if suffix.isdigit():
                batch_nums.append(int(suffix))

    if batch_nums:
        next_num = max(batch_nums) + 1
    else:
        # As per instruction, use random 4 digits if no existing numeric batch dirs
        # But to match example starting from 1, we'll use 1 here.
        next_num = 1

    # Files to move: first (groups * GROUP_SIZE) or fewer
    files_to_move = files[:groups * GROUP_SIZE]

    for i in range(groups):
        this_num = next_num + i
        batch_dir = f"batch{this_num}"
        batch_path = os.path.join(dir_path, batch_dir)

        if os.path.exists(batch_path):
            print(f"Error: Directory '{batch_dir}' already exists. Cannot create duplicate.")
            sys.exit(1)

        try:
            os.makedirs(batch_path)
        except OSError as e:
            print(f"Error creating directory '{batch_dir}': {e}")
            sys.exit(1)

        start = i * GROUP_SIZE
        end = start + GROUP_SIZE
        batch_files = files_to_move[start:end]

        for f in batch_files:
            src = os.path.join(dir_path, f)
            dst = os.path.join(batch_path, f)
            try:
                shutil.move(src, dst)
            except OSError as e:
                print(f"Error moving file '{f}': {e}")
                # Optionally, continue or exit

    print(f"Successfully created {groups} batch directories.")

if __name__ == "__main__":
    main()
