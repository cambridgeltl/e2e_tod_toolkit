# -*- coding: utf-8 -*-
"""
File Download and Extraction Utility

This utility script is designed to automate the process of downloading and extracting zip files from a specified URL.

Original Source: Open-source community contributions, from GPT-4.0
Modifications and Adaptation: Songbo Hu
Date: 15 December 2023
License: MIT License
"""

import requests
import zipfile
from io import BytesIO

def download_and_unzip(url, extract_to='./'):
    """
    Downloads a zip file from a given URL and unzips it to a specified directory.

    :param url: URL of the zip file to download.
    :param extract_to: Directory where to extract the contents of the zip file. Default is current directory.
    """
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(extract_to)
        print("File downloaded and unzipped successfully.")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")


if __name__ == '__main__':
    # Down the multi3woz dataset.
    url = 'https://github.com/cambridgeltl/multi3woz/blob/main/data.zip?raw=true'
    download_and_unzip(url)
