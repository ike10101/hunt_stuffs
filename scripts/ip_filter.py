import argparse
import ipaddress
import sys

def load_cidrs(cidr_file):
    networks = []
    with open(cidr_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    networks.append(ipaddress.ip_network(line, strict=False))
                except ValueError as e:
                    print(f"Warning: Invalid CIDR '{line}': {e}", file=sys.stderr)
    return networks

def filter_ips(ip_file, networks):
    with open(ip_file, 'r') as f:
        for line in f:
            ip_str = line.strip()
            if not ip_str:
                continue
            try:
                ip = ipaddress.ip_address(ip_str)
                if not any(ip in net for net in networks):
                    yield ip_str
            except ValueError as e:
                print(f"Warning: Invalid IP '{ip_str}': {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Filter IPs from a list by excluding those in specified CIDR ranges.")
    parser.add_argument('--ip-list', '-il', required=True, help="File containing list of IPs (one per line)")
    parser.add_argument('--cidr-list', '-cl', required=True, help="File containing CIDR ranges to filter out (one per line)")
    parser.add_argument('--output', '-o', default=None, help="Optional output file for filtered IPs (default: stdout)")
    parser.add_argument('--overwrite', '-ow', action='store_true', help="Overwrite the original ip-list file with filtered IPs")

    args = parser.parse_args()

    networks = load_cidrs(args.cidr_list)

    filtered_ips_gen = filter_ips(args.ip_list, networks)

    if args.overwrite:
        filtered_ips = list(filtered_ips_gen)
        with open(args.ip_list, 'w') as out_f:
            for ip in filtered_ips:
                out_f.write(ip + '\n')
        print(f"Overwrote {args.ip_list} with {len(filtered_ips)} filtered IPs.")
    elif args.output:
        with open(args.output, 'w') as out_f:
            for ip in filtered_ips_gen:
                out_f.write(ip + '\n')
    else:
        for ip in filtered_ips_gen:
            print(ip)

if __name__ == "__main__":
    main()