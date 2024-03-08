import os
import json
import re
from config import Config


class FileManager:

    # initialize the file manager with the provided path and metadata manager
    def __init__(self, base_path, meta_data_manager):
        self.config = Config(base_path)
        self.rawdata_path = "data/primary_data"
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
        #  retrieve and format raw title and source corpus from file name
        parts = file_name.split('.')
        title_raw = parts[1]
        source = parts[2]
        add_spaces = lambda s: re.sub(r'(?<!^)(?=[A-Z])', ' ', s).strip()
        au_name = add_spaces(au_name_raw)
        title_en = add_spaces(title_raw)
        parts[2] = re.sub(r'-ara\d*', '-ara', parts[2])
        text_id = f"{parts[1] + '.' + parts[2]}"

        # populate the metadata fields
        self.meta_data_manager.text_meta["text_id"] = text_id
        self.meta_data_manager.text_meta['title_auto'] = title_en
        self.meta_data_manager.text_meta["text_version"] = re.sub(r'-ara\d*', '-ara', source)
        self.meta_data_manager.text_meta["author_id"] = parts[0]
        self.meta_data_manager.author_meta["author_id"] = parts[0]
        self.meta_data_manager.author_meta['au_death_hij'] = au_date
        self.meta_data_manager.author_meta['author_auto'] = au_name
        return source

    # save data as JSON to a specified directory
    def save_meta_json(self, data, file_name, dir_path):
        os.makedirs(dir_path, exist_ok=True)
        clean_name = re.sub(r'-ara\d*', '', os.path.basename(file_name))
        json_file_name = os.path.join(dir_path, clean_name + '.json')
        with open(json_file_name, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
