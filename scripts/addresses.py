import csv

# Read the CSV file
with open('10248_out.csv', 'r') as file:
    reader = csv.reader(file)
    rows = list(reader)

# Assuming first row is ports
ports = [p.strip() for p in rows[0] if p.strip()]

# Find the maximum number of rows for any column
max_rows = max(len(row) for row in rows[1:]) if rows else 0

# Open output file
with open('10248_addrss', 'w') as outfile:
    # For each port index
    for port_idx in range(len(ports)):
        port = ports[port_idx]
        # Collect all IPs for this port from all rows
        for row in rows[1:]:
            if port_idx < len(row):
                ip = row[port_idx].strip()
                if ip:
                    outfile.write(f"{ip}:{port}\n")
