#!/usr/bin/env python3
import argparse
import sys

try:
    from googlesearch import search
except ImportError:
    print("Error: required module 'googlesearch' not found. Install with `pip install googlesearch-python`", file=sys.stderr)
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Perform a web search for a given dork/query and list URLs."
    )
    parser.add_argument('-q', required=True,
                        help='Search query (dork) to use')
    parser.add_argument('-max', type=int, default=50,
                        help='Maximum number of results to retrieve (default: 50)')
    parser.add_argument('-o', metavar='OUTPUTFILE',
                        help='Write results to OUTPUTFILE (no extension added)')
    return parser.parse_args()

def main():
    args = parse_args()

    try:
        # call search with positional query and num_results
        results = search(args.q, num_results=args.max)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.o:
            with open(args.o, 'w') as f:
                for url in results:
                    f.write(url + '\n')
        else:
            for url in results:
                print(url)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
