import sys
import csv
import ast
from collections import defaultdict
from ipaddress import ip_address

if len(sys.argv) != 3:
    print("Usage: python script.py <input_file> <output.csv>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]

# Parse the input file
ip_ports = {}
with open(input_file, 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        ip, ports_str = line.split(' -> ')
        ports = ast.literal_eval(ports_str)
        ip_ports[ip] = set(ports)

# Collect all unique ports
all_ports = set()
for ports in ip_ports.values():
    all_ports.update(ports)

# Compute counts for each port
port_counts = {}
for port in all_ports:
    count = sum(1 for ports in ip_ports.values() if port in ports)
    port_counts[port] = count

# Sort ports by count descending, then by port ascending
sorted_ports = sorted(all_ports, key=lambda p: (-port_counts[p], p))

# Collect sorted IPs for each port
port_ips = defaultdict(list)
all_ips = sorted(ip_ports.keys(), key=ip_address)
for ip in all_ips:
    for port in ip_ports[ip]:
        port_ips[port].append(ip)

# Note: since we loop over sorted ips, the ips in port_ips[port] are appended in sorted order

# Find max list length
max_len = max((len(port_ips[port]) for port in sorted_ports), default=0)

# Write to CSV
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Header row with ports
    writer.writerow(sorted_ports)
    # Data rows
    for i in range(max_len):
        row = []
        for port in sorted_ports:
            ips = port_ips[port]
            row.append(ips[i] if i < len(ips) else '')
        writer.writerow(row)
