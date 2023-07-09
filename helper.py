import os
import numpy as np
import logging
import sys
import json
import dns.resolver
from tldextract import extract
from datetime import datetime
from threading import Lock
from selenium.webdriver.chrome.options import Options


# The ugly/boring stuff. Load trackers, CDNs,chrome drive
def init_variables():
    global ALL_TRACKERS, CDNS, chrome_options, counter, counter_lock, n_domains, res_test
    # Trackers and CDNs.
    ALL_TRACKERS = set(np.loadtxt('data/trackers/all-sorted.txt', dtype=str))
    CDNS = set(['google', 'facebook', 'instagram', 'netflix', 'akamai', 'alibaba', 'cloudflare', 'amazon', 'cdnetworks', 'limelight', 'apple', 'twitter', 'msegde', 'fastly'])

    # Logging.
    logging.basicConfig(level=logging.INFO, format='%(message)s', filename=f'logs/{datetime.now().strftime("%Y-%m-%d@%H:%M:%S.log")}', force=True)
    logging.getLogger()

    # Webdriver options.
    chrome_options = Options()
    # For furure work. 
    # chrome_options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("ignore-certificate-errors")
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("incognito")
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument("disable-xss-auditor")
    chrome_options.add_argument("mute-audio")
    chrome_options.add_argument("disable-notifications")
    chrome_options.add_argument("allow-running-insecure-content")
    chrome_options.add_argument("--no-sandbox")

    # DNS resolver.
    res_test = dns.resolver.Resolver()
    res_test.nameservers = ['8.8.8.8']

    # Progress.
    counter = 0
    counter_lock = Lock()


# Strip webstite of any prefixes. https://wwww.exmaple.com/ -> example.com
def strip_website(website):
    return website.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')


# Return resolver.
def get_resolver():
    return res_test


# Return the chrome options.
def get_chrome_options():
    return chrome_options


# Change the global variable keeping track of the number of domains we're crawling.
def set_n_domains(n):
    global n_domains
    n_domains = n


# Return n_domains.
def get_n_domains():
    return n_domains


# Increment the progress counter.
def increment_counter():
    global counter
    with counter_lock:
        counter += 1
        print(f'\rDomains crawled: {counter}/{n_domains}', end='')


# Write to log file.
def log(msg):
    logging.getLogger().info(msg)


# Write to log file and print.
def log_print(msg):
    print(msg)
    logging.getLogger().info(msg)


# This function checks whether the given domain name is present in one of the CDNs lists.
def is_cdn(domain):
    return any(cdn in domain for cdn in CDNS)


# This function checks whether the given domain name is present in one of the trackers lists.
def is_tracker(domain_name: str) -> bool:
    # Strip the domain name of some prefixes.
    tld = extract_tld(domain_name)

    return tld in ALL_TRACKERS
    # Binary search.
    index = np.searchsorted(ALL_TRACKERS, tld)
    return bool(ALL_TRACKERS[index] == tld and index != len(ALL_TRACKERS))


# Extract the TLD from a domain name.
def extract_tld(domain_name):
    ext = extract(domain_name)
    return f"{ext.domain}.{ext.suffix}"


# Get the TTL of a domain.
def get_ttl(expiration_date):
    if expiration_date == -1:
        return -1
    return round(expiration_date - datetime.utcnow().timestamp())


# Read domains from csv file.
def read_domains(filename, partial):
    domains = [strip_website(x.split(',')[-1]) for x in np.loadtxt(filename, dtype=str)]
    return get_partial(domains, partial) if partial else domains


def construct_out_file(filename, out_folder, partial='', version=''):
    # Check if output folder exists.
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    if partial: partial = f'_{partial}'
    if version: version = f'_v{version}'
    out_file = f'{out_folder.rstrip("/")}/{filename.rsplit(".", 1)[0].split("/")[-1]}{partial}{version}'
    # Check if existing file should be overwritten.
    if os.path.exists(x := f'{out_file}.json'):
        overwrite = input(f'File {x} already exists. Overwrite? [y/n/v?]\n> ')
        # Overwrite existing file.
        if overwrite == 'y':
            return x

        # Version chosen by user.        
        if overwrite[0] == 'v':
            return f'{out_file}_{overwrite}.json'
        
        # Version chosen by program. Length of output folder.
        return f'{out_file}_{len(os.listdir(out_folder)) + 1}.json'

    # No existing file.
    return f'{out_file}.json'


# Write the CNAME chains to a json file.
def write_data(data, out_file):
    # Write dict to json file. 
    with open(out_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'\nWrote data to {out_file}')


# Get partial list of domains.
def get_partial(domains, partial_str):
    try:
        start, end = map(int, partial_str.split('-'))
        if end > len(domains):
            end = len(domains)
            log_print(f'Partial string is too large. Using {start}-{end} instead.')
            partial_str = f'{start}-{end}'

        end = min(end, len(domains))

        if end < start: raise ValueError
        return domains[start - 1:end]
    
    except ValueError:
        print('Invalid partial string. Please use the format "start-end".')
        sys.exit(1)
