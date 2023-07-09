# Analyzing the Use of CNAME Cloaking in the Wild

This repository is used for the Master's Thesis of Boris van Groeningen, supervised by Georgios Smaragdakis. Given an input file with a list of websites, this program finds all cookies and embedded objects for the given domain. It then analyzes the cookies and embedded objects to find out if they are third-party cookies, trackers, CDNs, malicious or if they are using CNAME cloaking.

## Requirements

The code if written in Python 3. During development, version 3.10 is used. An older version of Python 3 should work as well.
In order to use this program you need to have the following installed:

* dnspython
* numpy
* selenium

For your convenience, you can install all of these with the following command:

```bash
pip3 install -r requirements.txt
```

You would also need a [chromedriver](https://chromedriver.chromium.org/). This can be easily installed on mac with homebrew:

```bash
brew install --cask chromedriver
```

For other operating systems, please refer to the [chromedriver documentation](https://chromedriver.chromium.org/getting-started). Make sure it's the same version as your Chrome browser.

## How to run

You can run the **crawl.py** file with a number of threads of your choice. The default is 10 threads. The output folder is optional, if not specified, the the standard out/misc folder will be used. Partial runs are also possible, if you want to continue a previous run, for example '-p 101-200'. As well as running the same file multiple times without overriding the previous output via version. The program starts counting from 1 not 0.

```bash
python3 crawl.py input_file_path [-h] [-t N_THREADS] [-o OUT_FOLDER] [-p PARTIAL] [-v VERSION]
```

When having performed a crawl in parts, we can use the **merge_files.py** file to merge the output files into one file. This file can be used on the output files from **crawl.py**. The files must be in the same folder to do so.

```bash
python3 merge_files.py folder_path [-o OUTPUT_NAME]
```

After having gathered the data, we have several files that can be used for analysis. The file **check_cloaking.py** can be used on the output files from **crawl.py** to see how much cloaking hs been found.

```bash
python3 check_cloaking.py input_file_path [-h] [-w] [-l]
```

* -w: write the results to a file (consisting of only cloaking)
* -l: list the cloakers and how many times they were found

To see the origins of a given cloaker, whether cookie or embedded and the respective domains. You can use the **cloaking_origin.py** file. This file can be used on the output files from **crawl.py**.

```bash
python3 cloaking_origin.py input_file_path cloaking_domain
```

## Output

The data will be processed into the following format and stored in a JSON file as follows:

```json
{
    "website_name_1": {
        "cookies": {
            "domain_1": {
                "cookie_data": [
                    {
                        "name": "str", 
                        "expires": "int"
                    },
                    ... 
                ],
                "is_third_party": "bool",
                "is_tracker": "bool",
                "is_CDN": "bool",
                "chain": [
                    {
                        "domain": "str", 
                        "TTL": "int", 
                        "is_tracker": "bool", 
                        "is_CDN": "bool", 
                        "is_cloaking": "bool",
                        "IPs": ["only added if cloaking is true", ...]
                    },
                    ...,
                ]
            },
            "..." 
        },
        "embedded": {
            "domain_1": "chain",
            "..." 
        }
    },
    "website_name_2": {
        "..." 
    }
}
```

As seen above, all obtained cookies are have been assigned to their respective domain. This allows us to only look up the domain chain once for each found cookie domain.
