package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// Output directories (easily changeable)
const (
	URLsDir = "/storage/emulated/0/otx_urls"
	SubsDir = "/storage/emulated/0/"
	APIKey  = "6ceeca56254a2caefffdc1af3324a521f5da0d5b767ca491049bb7954e0b1a39"
)

// OTXResponse represents the API response structure
type OTXResponse struct {
	HasNext bool `json:"has_next"`
	URLList []struct {
		URL string `json:"url"`
	} `json:"url_list"`
}

// Config holds script configuration
type Config struct {
	SaveURLs bool
	SaveSubs bool
	Verbose  bool
	Timeout  int
	Threads  int
}

func main() {
	// Define flags
	var domain, domainListFile string
	var saveURLs, saveSubs, verbose bool
	var threads, timeout, maxPages int

	flag.StringVar(&domain, "d", "", "Specify a domain")
	flag.StringVar(&domainListFile, "l", "", "Specify a file containing a list of domains")
	flag.BoolVar(&saveURLs, "urls", false, "Save processed URLs to file")
	flag.BoolVar(&saveSubs, "subs", false, "Save extracted subdomains to file")
	flag.IntVar(&threads, "t", 2, "Number of domains to process concurrently (default 2 for list)")
	flag.BoolVar(&verbose, "v", false, "Verbose output")
	flag.IntVar(&timeout, "timeout", 45, "Timeout in seconds (default 45)")
	flag.IntVar(&maxPages, "page", 101, "Maximum number of pages to fetch (0 for unlimited)")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage of %s:\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()

	// Validate compulsory -d or -l flag
	if (domain != "" && domainListFile != "") || (domain == "" && domainListFile == "") {
		fmt.Println("Error: specify either -d or -l, but not both")
		flag.Usage()
		os.Exit(1)
	}

	// If neither --urls nor --subs is specified, enable both
	if !saveURLs && !saveSubs {
		saveURLs = true
		saveSubs = true
	}

	// Configure script
	config := &Config{
		SaveURLs: saveURLs,
		SaveSubs: saveSubs,
		Verbose:  verbose,
		Timeout:  timeout,
		Threads:  threads,
	}

	// Create HTTP client with timeout
	client := &http.Client{
		Timeout: time.Duration(timeout) * time.Second,
	}

	// Process single domain or list
	if domain != "" {
		processDomain(domain, config, client, maxPages)
	} else {
		domains, err := readDomainsFromFile(domainListFile)
		if err != nil {
			fmt.Println("Error reading domain list:", err)
			os.Exit(1)
		}
		processDomainsConcurrently(domains, config, client, maxPages)
	}
}

// readDomainsFromFile reads domains from a file
func readDomainsFromFile(file string) ([]string, error) {
	content, err := ioutil.ReadFile(file)
	if err != nil {
		return nil, err
	}
	lines := strings.Split(string(content), "\n")
	var domains []string
	for _, line := range lines {
		if d := strings.TrimSpace(line); d != "" {
			domains = append(domains, d)
		}
	}
	return domains, nil
}

// processDomainsConcurrently processes multiple domains using a worker pool
func processDomainsConcurrently(domains []string, config *Config, client *http.Client, maxPages int) {
	domainChan := make(chan string, len(domains))
	for _, d := range domains {
		domainChan <- d
	}
	close(domainChan)

	var wg sync.WaitGroup
	for i := 0; i < config.Threads; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for domain := range domainChan {
				processDomain(domain, config, client, maxPages)
			}
		}()
	}
	wg.Wait()
}

// processDomain fetches and processes URLs for a single domain
func processDomain(domain string, config *Config, client *http.Client, maxPages int) {
	if config.Verbose {
		fmt.Println("Processing domain:", domain)
	}

	urlSet := make(map[string]struct{})
	domainSet := make(map[string]struct{})

	for page := 1; ; page++ {
		apiURL := fmt.Sprintf("https://otx.alienvault.com/api/v1/indicators/domain/%s/url_list?limit=500&page=%d", domain, page)
		if config.Verbose {
			fmt.Println("Fetching page", page, "for domain", domain)
		}

		body, err := fetchPage(client, apiURL)
		if err != nil {
			fmt.Println("Error fetching URLs for domain", domain, "on page", page, ":", err)
			break
		}

		var result OTXResponse
		if err := json.Unmarshal(body, &result); err != nil {
			fmt.Println("Error decoding JSON for domain", domain, "on page", page, ":", err)
			continue
		}

		for _, entry := range result.URLList {
			// Remove protocol from URL
			urlNoProtocol := strings.TrimPrefix(entry.URL, "http://")
			urlNoProtocol = strings.TrimPrefix(urlNoProtocol, "https://")
			urlSet[urlNoProtocol] = struct{}{}

			// Extract subdomain
			u, err := url.Parse(entry.URL)
			if err == nil {
				if host := u.Hostname(); host != "" {
					domainSet[host] = struct{}{}
				}
			}
		}

		if !result.HasNext {
			break
		}
		if maxPages != 0 && page >= maxPages {
			break
		}
	}

	// Save URLs if requested
	if config.SaveURLs {
		saveToFile(urlSet, domain, URLsDir, config.Verbose)
	}

	// Save subdomains if requested
	if config.SaveSubs {
		saveToFile(domainSet, domain, SubsDir, config.Verbose)
	}
}

// fetchPage retrieves a page from the OTX API with retry on timeout
func fetchPage(client *http.Client, apiURL string) ([]byte, error) {
	req, err := http.NewRequest("GET", apiURL, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Add("X-OTX-API-KEY", APIKey)

	resp, err := client.Do(req)
	if err != nil {
		if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
			// Retry once
			req, err := http.NewRequest("GET", apiURL, nil)
			if err != nil {
				return nil, err
			}
			req.Header.Add("X-OTX-API-KEY", APIKey)
			resp, err = client.Do(req)
			if err != nil {
				return nil, fmt.Errorf("timeout after retry: %v", err)
			}
		} else {
			return nil, err
		}
	}
	defer resp.Body.Close()
	return ioutil.ReadAll(resp.Body)
}

// saveToFile writes sorted unique items to a file
func saveToFile(set map[string]struct{}, fileName, dir string, verbose bool) {
	var items []string
	for item := range set {
		items = append(items, item)
	}
	sort.Strings(items)

	filePath := filepath.Join(dir, fileName)
	file, err := os.Create(filePath)
	if err != nil {
		fmt.Println("Error creating file", filePath, ":", err)
		return
	}
	defer file.Close()

	for _, item := range items {
		fmt.Fprintln(file, item)
	}

	if verbose {
		fmt.Println("Saved to", filePath)
	}
}