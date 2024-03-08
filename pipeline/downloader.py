import os
import logging
import requests
import pandas as pd

# set up logging
logging.basicConfig(filename='download_logs.log', level=logging.INFO, format='%(asctime)s - %(message)s')


# function to download file
def download_file(url, destination_folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            filename = os.path.join(destination_folder, os.path.basename(url))
            with open(filename, 'wb') as file:
                file.write(response.content)
            logging.info(f"Downloaded: {url}")
            return True
        else:
            logging.error(f"Failed to download: {url}")
            return False
    except Exception as e:
        logging.exception(f"Exception occurred while downloading {url}: {e}")
        return False


# function to start downloading
def start_downloading(manifest_file, destination_folder):
    try:
        # read manifest file
        df = pd.read_excel(manifest_file, header=None,
                           usecols=[8])  # use header=None to avoid treating the first row as column names

        # iterate through each row in the manifest file
        for index, row in df.iterrows():
            file_url = row[8]  # access column 9 (index 8) for file URL
            if pd.notna(file_url):  # check if the URL is not NaN
                download_file(file_url, destination_folder)
    except Exception as e:
        logging.exception(f"Exception occurred while processing manifest file: {e}")


# Main function
def main():
    manifest_file = "manifest.xlsx"  # download manifest
    destination_folder = "allData"  # destination folder

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    start_downloading(manifest_file, destination_folder)


# Entry point of the script
if __name__ == "__main__":
    main()
