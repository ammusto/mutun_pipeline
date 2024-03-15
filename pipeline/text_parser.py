import os
import logging
import re
import json
import time
import pandas as pd
import multiprocessing

from concurrent.futures import ThreadPoolExecutor
from pipeline.metadata_manager import MetaDataManager
from pipeline.file_manager import FileManager
from pipeline.utility import Utility
from pipeline.markdown_cleaner import clean_text
from pipeline.camel_analyzer import TextAnalyzer
from camel_tools.disambig.mle import MLEDisambiguator
# from camel_tools.disambig.bert import BERTUnfactoredDisambiguator  # for BERT disambiguator


class TextParser:
    def __init__(self, path, log_file='file_processing.log', log_level=logging.INFO):
        self.master_metadata = pd.read_excel("master_meta.xlsx")  # load master metadata xlsx from OpenITI
        self.disambiguator = MLEDisambiguator.pretrained()
        # self.disambiguator = BERTUnfactoredDisambiguator.pretrained()  # for BERT disambiguator
        self.meta_data_manager = MetaDataManager(self.master_metadata)
        self.file_manager = FileManager(path, self.meta_data_manager)
        self.utility = Utility()
        self.page_count = 1
        self.last_vol_num = None
        self.last_page_num = 0
        self.total_tokens = 0

        logging.basicConfig(filename=log_file, level=log_level, format='%(asctime)s - %(message)s')

    def get_data_wrapper(self, raw_file):
        # use a thread pool for i/o-bound tasks within each process
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.get_data, raw_file)
            return future.result()

    # acquire list of text files to parse excluding those already processed

    def parse_directory(self, num_files=8000):
        print("Collecting filenames to be processed...")
        processed_files = self.file_manager.get_processed_files()
        all_files = os.listdir(self.file_manager.rawdata_path)
        filtered_files = [file for file in all_files if 'ara' in file and file not in processed_files]
        sorted_filtered_files = sorted(filtered_files)
        limited_files = sorted_filtered_files[:num_files]
        files_to_process = [os.path.join(self.file_manager.rawdata_path, item) for item in limited_files]
        print("Collecting done.")

        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            print("Processing files...")
            pool.map(self.get_data_wrapper, files_to_process)

        # for non-multiprocessing you can use this code but comment three lines above.
        #   print("Processing files...")
        # for file in files_to_process:
        #     self.get_data(file)

    # parse each page of a text

    def parse_page(self, page):
        chapters = []

        if not re.search(r"^$", page) and not re.search(r"a11b\d{2}a11b\d{3,}", page):
            page = page + "a11b00a11b000"

        line = page.strip()
        text, vol_num, page_num = line.rsplit("a11b", 2)

        # fix erroneous 00 volume

        if vol_num == "00" and self.last_vol_num is not None:
            vol_num = self.last_vol_num
        elif vol_num == "00" and self.last_vol_num is None:
            vol_num = "01"
        else:
            self.last_vol_num = vol_num.lstrip('0')

        # fix erroneous 000 page number

        if page_num == "000":
            page_num = str(int(self.last_page_num) + 1)

        self.last_page_num = page_num

        # fix erroneous paragraphing

        if text.startswith("</p><p>"):
            text = text[len("</p>"):]
        if text.endswith("</p><p>"):
            text = text[:-len("</p><p>")]

        # create list of chapters

        if "h1" in text:
            chapters = re.findall(r"<h1>(.*?)</h1>", text, re.DOTALL)

        return text, vol_num, page_num, chapters

    # parse cleaned text

    def parse_text(self, text, base_filename):
        cleaned_text = clean_text(text)

        if cleaned_text.splitlines()[0] == "a11b00a11b000":
            cleaned_text = '\n'.join(cleaned_text.splitlines()[1:])

        for line in cleaned_text.splitlines():
            parsed_data = self.parse_page(line)

            if parsed_data:
                text, vol_num, page_num, chapters = parsed_data

                analyzer = TextAnalyzer(text, self.disambiguator)
                tokens = analyzer.get_analysis_result()

                # create dictionary for all page data

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
                self.file_manager.save_page_json(page_data, base_filename, vol_num)
                self.page_count += 1

    # get all parsed data

    def get_data(self, raw_file):
        self.page_count = 1
        self.total_tokens = 0
        self.meta_data_manager.reset_metadata()
        text_id = self.file_manager.parse_file_name(raw_file)

        with open(raw_file, 'r', encoding='utf-8') as file:
            file_contents = file.read()
            base_filename = os.path.basename(raw_file)
            start_time = time.time()
            self.meta_data_manager.set_metadata(text_id)
            self.parse_text(file_contents, base_filename)  # parse text file for contents
            self.meta_data_manager.text_meta["page_count"] = self.page_count  # save total page_count
            jsons = [self.meta_data_manager.author_meta, self.meta_data_manager.text_meta]
            for data in jsons:
                self.utility.fill_empty_nodata(data)  # add string "NODATA" for empty metadata fields

        # save author and text metadata jsons

        self.file_manager.save_meta_json(self.meta_data_manager.author_meta, base_filename,
                                         self.file_manager.author_meta_path)
        self.file_manager.save_meta_json(self.meta_data_manager.text_meta, base_filename,
                                         self.file_manager.text_meta_path)

        end_time = time.time()
        logging.info(f"Processed data from file {base_filename}, with"
                     f" {self.meta_data_manager.text_meta['page_count']} pages."
                     f" Time taken: {end_time - start_time:.2f} seconds for {self.total_tokens} tokens"
                     f" at {self.total_tokens / (end_time - start_time):.2f} tokens/sec.")

        print(f"Processed {self.total_tokens} tokens from"
              f" {base_filename} in {end_time - start_time:.2f} seconds. "
              f"at {self.total_tokens / (end_time - start_time):.2f} tokens/sec.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process text files.')
    parser.add_argument('path', type=str, help='Path to the directory containing text files')
    parser.add_argument('--log', type=str, default='file_processing.log', help='Path to the log file')
    parser.add_argument('--log_level', type=str, default='INFO', help='Log level (e.g., DEBUG, INFO, WARNING, ERROR)')
    args = parser.parse_args()

    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('Invalid log level: %s' % args.log_level)

    text_parser = TextParser(args.path, args.log, log_level)
    text_parser.parse_directory()
