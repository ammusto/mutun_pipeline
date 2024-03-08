import os
import logging
import re
import json
import time
import multiprocessing

from concurrent.futures import ThreadPoolExecutor
from camel_tools.disambig.mle import MLEDisambiguator

from pipeline.metadata_manager import MetaDataManager
from pipeline.file_manager import FileManager
from pipeline.utility import Utility
from pipeline.name_parser import NameParser
from pipeline.markdown_cleaner import clean_text
from pipeline.camel_analyzer import TextAnalyzer

# set up logging

logging.basicConfig(filename='../file_processing.log', level=logging.INFO, format='%(asctime)s - %(message)s')


class TextParser:
    def __init__(self, path):
        self.meta_data_manager = MetaDataManager()
        self.file_manager = FileManager(path, self.meta_data_manager)
        self.utility = Utility()
        self.disambiguator = MLEDisambiguator.pretrained()
        self.name_parser = NameParser()
        self.page_count = 1
        self.last_vol_num = None
        self.last_page_num = 0
        self.total_tokens = 0

    # function for naming and saving json objects for each page of a text
    def save_page_json(self, page_data, base_filename, volume_num):
        output_folder = os.path.join(self.file_manager.text_content_path, base_filename)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        clean_name = re.sub(r'-ara\d*', '', base_filename)
        output_filename = f"{clean_name.split('.')[-1]}-{volume_num}-{page_data['page_num']}.json"  # set page file name
        output_file_path = os.path.join(output_folder, output_filename)
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(page_data, outfile, ensure_ascii=False, indent=4)

    def get_data_wrapper(self, raw_file):
        # use a thread pool for i/o-bound tasks within each process
        with ThreadPoolExecutor() as executor:
            future = executor.submit(self.get_data, raw_file)
            return future.result()

    # check logfile to get list of texts already parsed

    def get_processed_files(self):
        processed_files = set()
        if os.path.exists('../file_processing.log'):
            with open('../file_processing.log', 'r') as log_file:
                for line in log_file:
                    if "Processed data from file" in line:
                        filename = line.split("Processed data from file ")[1].split(",")[0].strip()
                        processed_files.add(filename)
        return processed_files

    # acquire list of text files to parse excluding those already processed

    def parse_directory(self, num_files=2000):
        processed_files = set(self.get_processed_files())
        all_files = os.listdir(self.file_manager.rawdata_path)
        filtered_files = [file for file in all_files if 'ara' in file and file not in processed_files]
        sorted_filtered_files = sorted(filtered_files)
        limited_files = sorted_filtered_files[:num_files]

        files_to_process = [os.path.join(self.file_manager.rawdata_path, item) for item in limited_files]
        # use multiprocessing for cpu-bound tasks
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            pool.map(self.get_data_wrapper, files_to_process)

    # parse each page of a text

    def parse_page(self, page):
        chapters = []
        line = page.strip()

        if not re.search(r"^$", page) and not re.search(r"a11b\d{2}a11b\d{3,}", page):
            page = page + "a11b00a11b000"  # adds pagination if pagination is missing

        if 'a11b' in page:  # check for pagination and volume marker
            text, vol_num, page_num = line.rsplit("a11b", 2)  # split line into page text, volume #, and page #

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
        else:
            return None

    # parse cleaned text

    def parse_text(self, text, base_filename):
        cleaned_text = clean_text(text)

        if cleaned_text.splitlines()[0] == "a11b00a11b000":
            cleaned_text = '\n'.join(cleaned_text.splitlines()[1:])  # remove erroneous paginations at start of file

        for line in cleaned_text.splitlines():  # parse each line of cleaned text which represents a single page
            parsed_data = self.parse_page(line)

            if parsed_data:
                text, vol_num, page_num, chapters = parsed_data

                analyzer = TextAnalyzer(text, self.disambiguator)
                tokens = analyzer.get_analysis_result()

                # create dictionary for all page data
                page_data = {
                    "text_id": self.meta_data_manager.text_meta["text_id"],
                    "author_id": self.meta_data_manager.text_meta["author_id"],
                    "volume_num": int(vol_num.lstrip('0')),
                    "page_num": int(page_num.lstrip('0')),
                    "page_text": text,
                    "chapter_headings": chapters,  # Adjust as necessary
                    "order": int(self.page_count),  # page_count is used for consecutively ordering each page in web app
                    "tokens": tokens
                }
                self.total_tokens += len(tokens)
                self.save_page_json(page_data, base_filename, vol_num)  # saves each page as individual JSON
                self.page_count += 1

    # get all parsed data

    def get_data(self, raw_file):
        source = self.file_manager.parse_file_name(raw_file)
        # create dictionary for assigning metadata parsing functions to appropriate texts

        meta_parsing_functions = {
            ("Shamela", "JK", "Shia", "PV", "Filaha"): self.meta_data_manager.parse_ssjpf,
            ("GRAR", "PAL", "ALCorpus", "JT", "MMS"): self.meta_data_manager.parse_gpajm,
            ("Hind", "Tafsir", "LAL"): self.meta_data_manager.parse_htl,
            ("Meshkat", "Rafed", "ShamIbad", "ShamAY", "Sham19", "Zaydiyya",
             "Masaha"): self.meta_data_manager.parse_mrssszm,
        }

        for source_prefixes, parse_function in meta_parsing_functions.items():
            if source.startswith(source_prefixes):
                with open(raw_file, 'r', encoding='utf-8') as file:
                    file_contents = file.read()
                    base_filename = os.path.basename(raw_file)
                    start_time = time.time()
                    parse_function(file_contents.splitlines())  # parse text file metadata headers
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
                             f"Time taken: {end_time - start_time:.2f} seconds"
                             f"Time per page:"
                             f" {(end_time - start_time) / self.meta_data_manager.text_meta['page_count']:.2f}."
                             f" Total tokens: {self.total_tokens}")

                print(f"Time to process"
                      f" {self.meta_data_manager.text_meta['page_count']} pages from"
                      f" {base_filename}: {end_time - start_time:.2f} seconds. "
                      f"Time per page:"
                      f" {(end_time - start_time) / self.meta_data_manager.text_meta['page_count']:.2f}."
                      f" Total tokens: {self.total_tokens}")

                break
