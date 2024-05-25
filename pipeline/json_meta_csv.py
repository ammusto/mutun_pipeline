import os
import json
import csv
import logging

# set up logging

logging.basicConfig(filename='json_to_csv.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# json folder
json_folder = '../json/author_meta'

# output CSV
output_csv = '../author_master.csv'


def load_json_data(json_folder):
    json_data = []
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            file_path = os.path.join(json_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                try:
                    data = json.load(json_file)
                    json_data.append(data)
                except json.JSONDecodeError as e:
                    logging.error(f"Error decoding JSON from file '{filename}': {e}")
    return json_data


def write_csv_data(csv_filename, data, fieldnames):
    with open(csv_filename, mode='w', newline='', encoding='utf-8-sig') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(data)


json_data = load_json_data(json_folder)
fieldnames = json_data[0].keys()
write_csv_data(output_csv, json_data, fieldnames)
