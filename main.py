import os
import multiprocessing
from config import Config
from pipeline.text_parser import TextParser
from camel_tools.disambig.mle import MLEDisambiguator
from camel_tools.disambig.bert import BERTUnfactoredDisambiguator

config = Config()

class ParserWorker:
    def __init__(self, disambiguator_type, use_gpu):
        if disambiguator_type == "BERT":
            self.disambiguator = BERTUnfactoredDisambiguator.pretrained(use_gpu=use_gpu, cache_size=1000000)
        else:
            self.disambiguator = MLEDisambiguator.pretrained()
        self.parser_instance = TextParser(self.disambiguator)

    def get_data(self, raw_file):
        return self.parser_instance.get_data(raw_file, self.parser_instance.disambiguator)

def get_processed_files():
    processed_files = set()
    if os.path.exists('file_processing.log'):
        with open('file_processing.log', 'r') as log_file:
            for line in log_file:
                if "Processed data from file" in line:
                    filename = line.split("Processed data from file ")[1].split(",")[0].strip()
                    processed_files.add(filename)
    return processed_files

def parse_directory(path, num_files=10000):
    print("Collecting filenames to be processed...")
    processed_files = set(get_processed_files())
    all_files = os.listdir(path)
    filtered_files = [file for file in all_files if 'ara' in file and file not in processed_files]
    sorted_filtered_files = sorted(filtered_files)
    limited_files = sorted_filtered_files[:num_files]
    files_to_process = [os.path.join(path, item) for item in limited_files]
    return files_to_process

def worker_init(disambiguator_type, use_gpu):
    global worker_instance
    worker_instance = ParserWorker(disambiguator_type, use_gpu)

def worker_func(raw_file):
    return worker_instance.get_data(raw_file)

if __name__ == "__main__":
    base_path = os.getcwd()
    files_to_process = parse_directory(config.rawdata_path)
    print("Collecting done.")

    if config.use_multiprocessing:
        with multiprocessing.Pool(processes=config.num_processes,
                                  initializer=worker_init,
                                  initargs=(config.disambiguator, config.use_gpu)) as pool:
            print(f"Processing files with multiprocessing...")
            pool.map(worker_func, files_to_process)
    else:
        print("Processing files without multiprocessing...")
        worker_instance = ParserWorker(config.disambiguator, config.use_gpu)
        for raw_file in files_to_process:
            worker_instance.get_data(raw_file)
