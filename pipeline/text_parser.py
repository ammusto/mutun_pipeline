import os
import logging
import re
import json
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from pipeline.metadata_manager import MetaDataManager
from pipeline.file_manager import FileManager
from pipeline.utility import Utility
from pipeline.markdown_cleaner import clean_text
from pipeline.camel_analyzer import TextAnalyzer

logging.basicConfig(filename='file_processing.log', level=logging.INFO, format='%(asctime)s - %(message)s')


class TextParser:
    def __init__(self, disambiguator):
        self.master_metadata = pd.read_excel("master_meta.xlsx")  # load master metadata xlsx from OpenITI
        self.meta_data_manager = MetaDataManager(self.master_metadata)
        self.disambiguator = disambiguator
        self.file_manager = FileManager(self.meta_data_manager)
        self.utility = Utility()
        self.page_count = 1
        self.last_vol_num = None
        self.last_page_num = 0
        self.total_tokens = 0

    def save_page_json(self, page_data, base_filename, volume_num):
        output_folder = os.path.join(self.file_manager.text_content_path, base_filename)
        os.makedirs(output_folder, exist_ok=True)
        clean_name = re.sub(r'-ara\d*', '', base_filename)
        output_filename = f"{clean_name.split('.')[-1]}-{volume_num}-{page_data['page_num']}.json"
        output_file_path = os.path.join(output_folder, output_filename)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(page_data, outfile, ensure_ascii=False, indent=4)

    def parse_page(self, page):
        chapters = []
        if not re.search(r"^$", page) and not re.search(r"a11b\d{2}a11b\d{3,}", page):
            page = page + "a11b00a11b000"
        line = page.strip()
        text, vol_num, page_num = line.rsplit("a11b", 2)

        if vol_num == "00" and self.last_vol_num is not None:
            vol_num = self.last_vol_num
        elif vol_num == "00" and self.last_vol_num is None:
            vol_num = "01"
        else:
            self.last_vol_num = vol_num.lstrip('0')

        if page_num == "000":
            page_num = str(int(self.last_page_num) + 1)
        self.last_page_num = page_num

        if text.startswith("</p><p>"):
            text = text[len("</p>"):]
        if text.endswith("</p><p>"):
            text = text[:-len("</p><p>")]

        if "h1" in text:
            chapters = re.findall(r"<h1>(.*?)</h1>", text, re.DOTALL)
        return text, vol_num, page_num, chapters

    def parse_text(self, text, base_filename, disambiguator):
        cleaned_text = clean_text(text)
        lines = cleaned_text.splitlines()
        if lines and lines[0] == "a11b00a11b000":
            lines = lines[1:]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.parse_and_save_line, line, base_filename, disambiguator) for line in lines]
            for future in futures:
                future.result()

    def parse_and_save_line(self, line, base_filename, disambiguator):
        parsed_data = self.parse_page(line)
        if parsed_data:
            text, vol_num, page_num, chapters = parsed_data
            analyzer = TextAnalyzer(text, disambiguator)
            tokens = analyzer.get_analysis_result()

            if isinstance(tokens, dict) and "error" in tokens:
                logging.error(
                    f"Error processing page {page_num} of volume {vol_num} in file {base_filename}: {tokens['error']}")
                return

            page_data = {
                "text_uri": self.meta_data_manager.text_meta["text_uri"],
                "text_id": self.meta_data_manager.text_meta["text_id"],
                "volume_num": int(vol_num.lstrip('0')),
                "page_num": int(page_num.lstrip('0')),
                "page_text": text,
                "chapter_headings": chapters,
                "order": int(self.page_count),
                "tokens": tokens
            }
            self.total_tokens += len(tokens)
            self.save_page_json(page_data, base_filename, vol_num)
            self.page_count += 1

    def get_data(self, raw_file, disambiguator):
        self.page_count = 1
        self.total_tokens = 0
        self.meta_data_manager.reset_metadata()
        text_id = self.file_manager.parse_file_name(raw_file)

        with open(raw_file, 'r', encoding='utf-8') as file:
            file_contents = file.read()
            base_filename = os.path.basename(raw_file)
            start_time = time.time()
            self.meta_data_manager.set_metadata(text_id)
            self.parse_text(file_contents, base_filename, disambiguator)
            self.meta_data_manager.text_meta["page_count"] = self.page_count
            jsons = [self.meta_data_manager.author_meta, self.meta_data_manager.text_meta]
            for data in jsons:
                self.utility.fill_empty_nodata(data)

        self.file_manager.save_meta_json(self.meta_data_manager.author_meta, base_filename,
                                         self.file_manager.author_meta_path)
        self.file_manager.save_meta_json(self.meta_data_manager.text_meta, base_filename,
                                         self.file_manager.text_meta_path)

        end_time = time.time()
        logging.info(f"File {base_filename};"
                     f" {self.meta_data_manager.text_meta['page_count']} pgs;"
                     f" {self.total_tokens} toks;"
                     f" {end_time - start_time:.2f} secs;"
                     f" {self.total_tokens / (end_time - start_time):.2f} tok/sec")

        print(f"Processed {self.total_tokens} tokens from"
              f" {base_filename} in {end_time - start_time:.2f} seconds. "
              f"at {self.total_tokens / (end_time - start_time):.2f} tokens/sec.")
