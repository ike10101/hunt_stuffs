#!/usr/bin/python3
import requests
import argparse
import time
import os
import re

# Keeps track of key sleep status
token_sleep_until = {}

def fetch_domain_report(domain, api_key, timeout, verbose):
    url = f"https://www.virustotal.com/vtapi/v2/domain/report?apikey={api_key}&domain={domain}"
    try:
        response = requests.get(url, timeout=timeout)
        if not response.text.strip():
            if verbose:
                print(f"Empty response for domain {domain} — treating as rate limit (204)")
            return {"response_code": 204}
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"Request error for domain {domain}: {e}")
        return {"response_code": -1, "error": str(e)}
    except ValueError:
        if verbose:
            print(f"Invalid JSON for domain {domain} — treating as rate limit (204)")
        return {"response_code": 204}

def extract_urls(report, all_urls, verbose):
    if not report or report.get("response_code") != 1:
        if verbose and report:
            print(f"Invalid or error response: {report.get('verbose_msg', 'Unknown error')}")
        return []
    if all_urls:
        urls = [url[0] for url in report.get("undetected_urls", []) + report.get("detected_urls", []) if isinstance(url, (list, tuple)) and len(url) > 0]
    else:
        urls = [url[0] for url in report.get("undetected_urls", []) if isinstance(url, (list, tuple)) and len(url) > 0]
    return urls

def main():
    parser = argparse.ArgumentParser(
        description="""
VirusTotal Domain Report Fetcher (v2 API)

Fetches domain reports from VirusTotal using the v2 API and extracts URLs.
By default, extracts only undetected URLs. Use --all to extract all URLs.
API keys can be provided via -k as a comma-separated list or a file.
""",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-d", "--domain", help="Specify a single domain")
    parser.add_argument("-l", "--list", help="Specify a file containing a list of domains")
    parser.add_argument("-k", "--keys", required=True, help="Comma-separated API keys or path to a file with API keys")
    parser.add_argument("--all", action="store_true", help="Extract all URLs (undetected and detected)")
    parser.add_argument("-o", "--output", help="Save output to a file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-timeout", type=int, default=50, help="Request timeout in seconds (default: 50)")
    parser.add_argument("-retries", type=int, default=0, help="Number of retries for failed requests (default: 0)")
    parser.add_argument("-log", help="Save domains with request failures (network errors, HTTP errors, etc.) to this file")

    args = parser.parse_args()

    if os.path.isfile(args.keys):
        with open(args.keys, "r") as file:
            api_keys = [line.strip() for line in file.readlines() if line.strip()]
    else:
        api_keys = args.keys.split(",")

    if not api_keys:
        print("Error: At least one API key must be provided.")
        exit(1)

    if args.domain:
        domains = [args.domain]
    elif args.list:
        with open(args.list, "r") as file:
            domains = [line.strip() for line in file.readlines() if line.strip()]
    else:
        print("Error: Either -d or -l must be specified.")
        exit(1)

    timestamps = {key: [] for key in api_keys}
    sleep_until = {key: 0 for key in api_keys}
    current_key_index = 0
    all_extracted_urls = []
    failed_domains = []

    try:
        for domain in domains:
            while True:
                api_key = api_keys[current_key_index]
                now = time.time()

                if now < sleep_until[api_key]:
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    if all(now < sleep_until[k] for k in api_keys):
                        wait_time = min(sleep_until[k] for k in api_keys) - now
                        if args.verbose:
                            print(f"All API keys are sleeping. Waiting {wait_time:.2f} seconds.")
                        time.sleep(wait_time)
                    continue

                ts_list = timestamps[api_key]
                ts_list = [t for t in ts_list if now - t < 60]
                if len(ts_list) >= 4:
                    sleep_until[api_key] = ts_list[0] + 60
                    continue

                if args.verbose:
                    print(f"\nProcessing domain: {domain} with API key {current_key_index}")

                report = fetch_domain_report(domain, api_key, args.timeout, args.verbose)
                timestamps[api_key].append(time.time())

                if report.get("response_code") == 204:
                    sleep_until[api_key] = time.time() + 60
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    continue

                if report.get("response_code") == -1:
                    failed_domains.append(domain)
                    break

                urls = extract_urls(report, args.all, args.verbose)
                all_extracted_urls.extend(urls)

                if args.verbose and report.get("response_code") == 1:
                    print(f"Extracted {len(urls)} URLs for domain {domain}")

                break
    except KeyboardInterrupt:
        if args.verbose:
            print("\nExecution interrupted. Saving partial results...")

    processed_urls = sorted(set(re.sub(r'^https?://', '', url) for url in all_extracted_urls))

    if args.verbose:
        print(f"\nTotal unique URLs extracted: {len(processed_urls)}")

    if args.output:
        with open(args.output, "w") as file:
            for url in processed_urls:
                file.write(url + "\n")
    else:
        for url in processed_urls:
            print(url)

    if args.log and failed_domains:
        with open(args.log, "w") as file:
            for domain in failed_domains:
                file.write(domain + "\n")

if __name__ == "__main__":
    main()
