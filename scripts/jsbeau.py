#!/usr/bin/env python3
import os
import sys
import argparse
import jsbeautifier

def beautify_file(input_path, output_path=None, verbose=False):
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {input_path}: {e}", file=sys.stderr)
        return

    try:
        beautified = jsbeautifier.beautify(content)
    except Exception as e:
        print(f"Error beautifying file {input_path}: {e}", file=sys.stderr)
        return

    target = output_path or input_path
    try:
        with open(target, 'w', encoding='utf-8') as f:
            f.write(beautified)
        if verbose:
            if output_path:
                print(f"Beautified '{input_path}' → '{output_path}'")
            else:
                print(f"Beautified '{input_path}' (in-place)")
    except Exception as e:
        print(f"Error writing file {target}: {e}", file=sys.stderr)

def process_directory(directory, traverse=False, verbose=False):
    try:
        if traverse:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith('.js'):
                        path = os.path.join(root, file)
                        beautify_file(path, verbose=verbose)
        else:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isfile(full_path) and file.lower().endswith('.js'):
                    beautify_file(full_path, verbose=verbose)
    except Exception as e:
        print(f"Error processing directory {directory}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Beautify JavaScript files using jsbeautifier')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--input', help='Input JS file to beautify')
    group.add_argument('-d', '--directory', help='Directory of JS files to beautify')
    parser.add_argument('-o', '--output', help='Output file path (only with -i)')
    parser.add_argument('--traverse', action='store_true', help='Traverse sub-directories (only with -d)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show processing/success messages')

    args = parser.parse_args()

    # Validate flag combinations
    if args.output and not args.input:
        print("Error: -o can only be used with -i", file=sys.stderr)
        sys.exit(1)
    if args.traverse and not args.directory:
        print("Error: --traverse can only be used with -d", file=sys.stderr)
        sys.exit(1)

    # Process
    if args.input:
        if not os.path.isfile(args.input):
            print(f"Error: Input file '{args.input}' does not exist", file=sys.stderr)
            sys.exit(1)
        beautify_file(args.input, args.output, verbose=args.verbose)
    else:
        if not os.path.isdir(args.directory):
            print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
            sys.exit(1)
        process_directory(args.directory, traverse=args.traverse, verbose=args.verbose)

if __name__ == '__main__':
    main()
