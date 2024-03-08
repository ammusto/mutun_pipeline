import os
from config import Config
from pipeline.text_parser import TextParser

if __name__ == "__main__":
    base_path = os.getcwd()
    config = Config(base_path)
    parser = TextParser(config)
    parser.parse_directory()
