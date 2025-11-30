import re
import argparse
import os

def extract_and_process_domains(input_file, mode='print'):
    """Extract and process domains from a single input file and either print to stdout or overwrite the file."""
    try:
        # Pattern to match "http://", "https://", "http://www." or "https://www."
        pattern = re.compile(r'https?://(?:www\.)?')

        final_domains = []

        # Step 1: Extract domains using the boundaries
        with open(input_file, 'r') as infile:
            for line in infile:
                parts = pattern.split(line)
                for part in parts[1:]:  # Skip the first part before the first URL
                    domain = part.strip()
                    # Step 2: Remove the first "/" and everything after it
                    domain = domain.split('/')[0]
                    final_domains.append(domain)

        if mode == 'print':
            # Print the final cleaned domains to stdout
            for domain in final_domains:
                print(domain)
        elif mode == 'overwrite':
            # Overwrite the input file with the final cleaned domains
            with open(input_file, 'w') as outfile:
                for domain in final_domains:
                    outfile.write(domain + '\n')

    except Exception as e:
        print(f"Error processing file '{input_file}': {e}")


def process_directory(directory):
    """Process all text files in the specified directory."""
    try:
        if not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a valid directory.")
            return

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                extract_and_process_domains(file_path, mode='overwrite')
        print("Directory processing completed successfully.")
    except Exception as e:
        print(f"Error processing directory '{directory}': {e}")


def main():
    parser = argparse.ArgumentParser(description="Extract and process domains from clustered URLs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-i', '--input', help="Input text file with clustered URLs. Output will be printed to stdout; redirect to a file using > output.txt.")
    group.add_argument('-d', '--directory', help="Directory containing text files to process. Files will be processed in place, overwriting them with the extracted domains.")

    args = parser.parse_args()

    if args.input:
        if not os.path.isfile(args.input):
            print(f"Error: '{args.input}' is not a valid file.")
            return
        extract_and_process_domains(args.input, mode='print')
    elif args.directory:
        process_directory(args.directory)


if __name__ == '__main__':
    main()