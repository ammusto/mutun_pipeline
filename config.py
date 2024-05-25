import os

class Config:
    def __init__(self):
        self.disambiguator = "BERT"  # "BERT" for the BER disambiguator or "MLE" for MLE disambiguator
        self.base_path = os.getcwd()
        self.rawdata_path = 'data/primary_data'
        self.author_meta_path = 'json/author_meta'
        self.text_meta_path = 'json/text_meta'
        self.text_content_path = 'json/text_content'
        self.use_gpu = True
        self.use_multiprocessing = True  # Set this to False to disable multiprocessing
        self.num_processes = 7  # Set the number of processes to use
