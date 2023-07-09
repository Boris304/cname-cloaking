import argparse
import concurrent.futures
from time import perf_counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from urllib.parse import urlparse
from helper import *


# Gets the IPs for a domain.
def get_ips(domain):
    try:
        answers = get_resolver().resolve(domain, 'A', lifetime=20)
        ips = [a_record.address for a_record in answers]
        return ips
    except: return []


# Do a DNS query to get the CNAME chain for a domain. Keep going until there is no CNAME record.
def find_chain(domain):
    original_tld = extract_tld(domain)
    chain = []
    traversed = set([domain])
    while True:
        try:
            answers = get_resolver().resolve(domain, 'CNAME', lifetime=20)
            if len(answers) > 1:
                log_print(f'Found multiple CNAME records for {domain}')
            cname = answers[0].target.to_text().strip('.')

            # Loop detected. Should never happen.
            if cname in traversed:
                log_print(f'\nLoop detected at {domain} - Start of chain: {traversed[0]}')
                return chain
            domain = cname
            
            # Check if the domain is a tracker or CDN.
            tld = extract_tld(domain)
            chain_node = {'domain': domain, 'TTL': answers.ttl, 'is_tracker': is_tracker(tld), 'is_CDN': is_cdn(domain)}

            # Check if the domain is cloaking.
            chain_node['is_cloaking'] = chain_node['is_tracker'] and tld != original_tld
            if chain_node['is_cloaking']:
                chain_node['IPs'] = get_ips(domain)
    
            # Add the chain node to the chain.
            chain.append(chain_node)
            traversed.add(domain)

        # No CNAME record found. We're done.
        except:
            return chain


# Extract the cookie and embedded data.
def get_cookies_embedded(driver, url, website_name, fields):
    # Connect to the website and get all cookies. Must enter empty dict as input arguments.
    driver.get(url)
    cookies = driver.execute_cdp_cmd('Network.getAllCookies', dict())['cookies']
    
    # Initialize dictionary to store cookie and embedded object data.
    wanted_data = {'cookies': {}, 'embedded': []}

    # Loop over all cookies found.
    for c in cookies:
        # Only keeping the fields we want (i.e. name and expires).
        cookie_data_dict = {k: c[k] for k in fields}
        # Convert expiring date to TTL. Keep -1 if it is a session cookie.
        cookie_data_dict['expires'] = get_ttl(cookie_data_dict['expires'])
        # Domain might start with '.'. Remove it.
        domain_name = c['domain'].strip('.')

        # Add the domain to the dictionary if it is not already there.
        if not domain_name in wanted_data['cookies']:
            wanted_data['cookies'][domain_name] = {'cookie_data': [], 'chain': []}
        
        # Add the cookie data to the dictionary.
        wanted_data['cookies'][domain_name]['cookie_data'].append(cookie_data_dict)
        wanted_data['cookies'][domain_name]['is_third_party'] = website_name not in c['domain']
        wanted_data['cookies'][domain_name]['is_tracker'] = is_tracker(c['domain'])
        wanted_data['cookies'][domain_name]['is_CDN'] = is_cdn(c['domain'])

    # Add chains to cookie domains. Cookies are already grouped by domain at this point.
    for domain in wanted_data['cookies']:
        wanted_data['cookies'][domain]['chain'] = find_chain(domain)

    # Get all embedded objects (hrefs).
    hrefs = driver.find_elements(By.XPATH, "//a[@href]")

    # Get all unique domains from the hrefs. Paths are removed to avoid duplicates.
    embedded = {domain for href in hrefs if (attr := href.get_attribute('href')) and (domain := urlparse(attr).netloc) and website_name not in domain}
    # Get the CNAME chain for each domain. DNS resulotion.
    embedded_chain = {domain: find_chain(domain) for domain in embedded}
    # Add it to the wanted data.
    wanted_data['embedded'] = embedded_chain
                
    return dict(wanted_data)
    

# Crawl a single website.
def crawl(website):
    all_cookies = {}
    # Can add more fields if needed. Can also move this to a config file/arguments.
    fields = ['name', 'expires']

    # Create new driver because it will otherwise return all the cookies from previous domains. 
    driver = webdriver.Chrome(options=get_chrome_options())
    # driver.set_page_load_timeout(100)
    target_url = f'https://www.{website}'
    try:
        all_cookies[website] = get_cookies_embedded(driver, target_url, website, fields)

    except (WebDriverException, TimeoutException):
            log(f'Could not load page: {website}')
            
    driver.quit()
    increment_counter()

    return all_cookies


# Divide the domains into chunks and start the threads.
def threading(domains, n_threads):
    # Threadpool takes care of most of the threading.
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        d_list = executor.map(crawl, domains)
    
    result = {}
    # Merge the results from the different chunks.
    for d in d_list: result.update(d)

    return result
    

# Main function.
def main(filename, n_threads, out_folder, partial_str, version):
    # Determine output file name.
    out_file = construct_out_file(filename, out_folder, partial_str, version)

    # Reading.
    domains = read_domains(filename, partial_str)
    
    # Set the number of domains to crawl. Used for progress counter.
    set_n_domains(len(domains))

    # Threading.
    data = threading(domains, n_threads)
    write_data(data, out_file)


# Start the program.
if __name__ == '__main__':
    start = perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='input file path')
    parser.add_argument('-t', '--n_threads', type=int, default=20, help='number of threads')
    parser.add_argument('-o', '--out_folder', default='out/misc', type=str, help='output folder path')
    parser.add_argument('-p', '--partial', type=str, default='', help='take slice of domains, start count at 1')
    parser.add_argument('-v', '--version', type=str, default='', help='version of the output file')
    args = parser.parse_args()
    init_variables()
    log(f'Arguments: {vars(args)}')
    main(args.filename, args.n_threads, args.out_folder, args.partial, args.version)
    end = perf_counter()
    print(f'Elapsed time: {end - start:.2f} seconds. Average time per domain: {(end - start) / get_n_domains():.2f} seconds.')
