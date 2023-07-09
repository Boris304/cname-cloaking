import json
import argparse
from helper import extract_tld


# Main func.
def main(filename, cloaking_domain):
    with open(filename) as f:
        data = json.load(f)

    origins = {'cookies': {}, 'embedded': {}}
    for website in data:

        # Check cookies.
        for domain in data[website]['cookies']:
            for node in data[website]['cookies'][domain]['chain']:
                if node['is_cloaking']:
                    if cloaking_domain in extract_tld(node['domain']):
                        origins['cookies'][domain] = origins['cookies'].get(domain, 0) + 1
                        continue

        # Check embedded.
        for domain in data[website]['embedded']:
            for node in data[website]['embedded'][domain]:
                if node['is_cloaking']:
                    if cloaking_domain in extract_tld(node['domain']):
                        origins['embedded'][domain] = origins['embedded'].get(domain, 0) + 1
                        continue

    # Print results.
    print('Cookies:')
    for origin, times in origins['cookies'].items():
        print(f'{times} -> {origin}')

    print('\nEmbedded:')
    for origin, times in origins['embedded'].items():
        print(f'{times} -> {origin}')


if __name__ == '__main__':
    # Parse arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='File containing the domains to crawl.')
    parser.add_argument('cloaking_domain', help='The cloaking domain to look for.')
    args = parser.parse_args()
    main(args.filename, extract_tld(args.cloaking_domain))
