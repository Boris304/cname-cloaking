import json
import argparse


# Keep only the websites and cookies/embedded objects that have cloaking.
def keep_cloaking(data, print_double_cloaking=False):
    cloaked_trackers = {}
    d = {}

    for website in data:
        on_this_website = set()

        # Check cookies.
        website_dict = {'cookies': {}, 'embedded': {}}
        for domain in data[website]['cookies']:
            for node in data[website]['cookies'][domain]['chain']:
                if node['is_cloaking'] and 'cedexis' not in node['domain']:
                    website_dict['cookies'][domain] = data[website]['cookies'][domain]
                    cloaked_trackers[node['domain']] = cloaked_trackers.get(node['domain'], 0) + 1
                    on_this_website.add(node['domain'])

        # Check embedded.
        for domain in data[website]['embedded']:
            for node in data[website]['embedded'][domain]:
                if node['is_cloaking'] and 'cedexis' not in node['domain']:
                    website_dict['embedded'][domain] = data[website]['embedded'][domain]
                    # cloaked_trackers[node['domain']] = cloaked_trackers.get(node['domain'], 0) + 1
                    if node['domain'] not in on_this_website:
                        cloaked_trackers[node['domain']] = cloaked_trackers.get(node['domain'], 0) + 1
                        on_this_website.add(node['domain'])

                    elif print_double_cloaking:
                        print(f'Found cloaking on {website} for {node["domain"]} but already found on this website.')
                    

        # Add if cloaking found.
        if website_dict['cookies'] or website_dict['embedded']:
            d[website] = website_dict

    # Original data with just cloakers. And counting the times the cloakers were found.
    return d, cloaked_trackers


# List the cloakers and how many times they were found.
def print_trackers(cloaked_trackers):
    print('Cloaked trackers:')
    cloaked_trackers = dict(sorted(cloaked_trackers.items(), key=lambda item: item[1], reverse=True))
    for tracker, times in cloaked_trackers.items():
        print(f'{times} -> {tracker}')


# Write to file.
def write_to_file(cloaked_data, filename):
    out_file = f'{filename.rstrip(".json")}_cloaking.json'
    with open(out_file, 'w') as f:
        json.dump(cloaked_data, f, indent=2)

    print(f'Wrote cloaking data to {out_file}')


# Main function.
def main(filename, write, list_trackers):
    with open(filename) as f:
        data = json.load(f)

    cloaked_data, cloaked_trackers = keep_cloaking(data, print_double_cloaking=False)

    # List trackers if wanted.
    if list_trackers:
        print_trackers(cloaked_trackers)

    print(f'Cloaking detected in {len(cloaked_data)} out of {len(data)} websites ({len(cloaked_data) / len(data) * 100:.2f}%).')
    
    # Write if wanted.
    if write:
       write_to_file(cloaked_data, filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='input file path')
    parser.add_argument('-w', help='to write to a file or not', default=False, action='store_true', dest='write')
    parser.add_argument('-l', help='list trackers', default=False, action='store_true', dest='list_trackers')
    args = parser.parse_args()
    main(args.filename, args.write, args.list_trackers)
