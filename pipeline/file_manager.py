import os
import json
import re
from config import Config


class FileManager:

    # initialize the file manager with the provided path and metadata manager
    def __init__(self, meta_data_manager):
        self.config = Config()
        self.rawdata_path = self.config.rawdata_path
        self.meta_data_manager = meta_data_manager
        self.author_meta_path = self.config.author_meta_path
        self.text_meta_path = self.config.text_meta_path
        self.text_content_path = self.config.text_content_path

    # arse the file name and extract information
    def parse_file_name(self, full_path):
        file_name = os.path.basename(full_path)
        match = re.match(r'(\d{4})([A-Za-z]+)', file_name)
        if match:
            au_death_hijri, au_name_raw = match.groups()
        else:
            raise ValueError("filename does not match expected pattern")

        au_date = au_death_hijri.lstrip('0')  # strip leading 0 from deathdate
        parts = file_name.split('.')
        text_id = re.sub(r'-ara\d*', '', parts[2])

        # populate the metadata fields
        self.meta_data_manager.text_meta["text_uri"] = file_name
        self.meta_data_manager.text_meta["text_id"] = text_id
        self.meta_data_manager.text_meta["author_id"] = parts[0]
        self.meta_data_manager.author_meta["author_id"] = parts[0]
        self.meta_data_manager.author_meta['au_death'] = au_date
        return text_id

    # save data as JSON to a specified directory
    def save_meta_json(self, data, file_name, dir_path):
        os.makedirs(dir_path, exist_ok=True)
        clean_name = re.sub(r'-ara\d*', '', os.path.basename(file_name))
        json_file_name = os.path.join(dir_path, clean_name + '.json')
        with open(json_file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    # check logfile to get list of texts already parsed used in text_parser

    def get_processed_files(self):
        processed_files = set()
        log_file = 'file_processing.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as log_file:
                for line in log_file:
                    if "Processed data from file" in line:
                        filename = line.split("Processed data from file ")[1].split(",")[0].strip()
                        processed_files.add(filename)
        return processed_files

    # function for naming and saving json objects for each page of a text used in text_parser

    def save_page_json(self, page_data, base_filename, volume_num):
        output_folder = os.path.join(self.text_content_path, base_filename)
        os.makedirs(output_folder, exist_ok=True)
        clean_name = re.sub(r'-ara\d*', '', base_filename)
        output_filename = f"{clean_name.split('.')[-1]}-{volume_num}-{page_data['page_num']}.json"
        output_file_path = os.path.join(output_folder, output_filename)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(page_data, outfile, ensure_ascii=False, indent=4)