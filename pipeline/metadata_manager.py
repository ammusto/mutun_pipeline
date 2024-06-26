import pandas as pd
import re
from pipeline.name_parser import NameParser

class MetaDataManager:
    def __init__(self, df):
        self.df = df
        self.author_meta = {
            "author_id": "", "author_ar": "", "author_ar_shuhra": "", "author_lat": "", "author_lat_shuhra": "",
            "author_auto": "", "au_death": ""
        }
        self.text_meta = {
            "text_id": "", "text_uri": "", "title_ar": "", "title_lat": "", "author_id": "", "ed_info": "",
            "collection": "", "tok_length": "", "page_count": "", "volumes": "", "tags": ""
        }
        self.name_parser = NameParser()

    def reset_metadata(self):
        # Reset author_meta dictionary
        for key in self.author_meta:
            self.author_meta[key] = ""

        # Reset text_meta dictionary
        for key in self.text_meta:
            self.text_meta[key] = ""

    def set_metadata(self, text_id):
        metadata = self.fetch_metadata(text_id)

        collection_mappings = {
            'ALCorpus': 'Arabic and Latin',
            'AOCP': 'Arabic OCR Catalyst Project',
            'ArabCommAph': 'Arabic Hippocratic Aphorisms',
            'BibleCorpus': 'Bible Corpus',
            'DARE': 'Digital Averroes',
            'DSS': 'Dept. of Syriac Studies',
            'EScr': 'Escriptorium',
            'Filaha': 'The Filāḥa Project',
            'JMIHE': 'Jewish-Muslim History',
            'Kraken': 'Kraken',
            'GRAR': 'Graeco-Arabic Studies',
            'Hindawi': 'Hindāwī',
            'JK': 'al-Jāmiʿ al-Kabīr',
            'LAL': 'Library of Arabic Lit.',
            'Masaha': 'Masāḥa',
            'MP': 'Muslim Philosophy',
            'SAWS': 'Sharing Ancient Wisdoms',
            'PAL': 'Ptolemaeus Arabus',
            'Sham': 'al-Maktaba al-Shāmila',
            'Sham30K': 'al-Maktaba al-Shāmila 30k',
            'ShamAY': 'al-Maktaba al-Shāmila AY',
            'ShamIbadiyya': 'al-Shāmila al-Ibāḍiyya',
            'Shamela': 'al-Maktaba al-Shāmila',
            'Shia': 'al-Shāmila al-Shīʿiyya',
            'Tafsir': 'al-Tafāsīr',
            'Wiki': 'Wīkī Maṣdar',
            'Zaydiyya': 'al-Shāmila al-Zaydiyya'
        }

        if metadata:
            # Extract metadata and update dictionaries
            self.author_meta["author_lat"] = metadata.get("author_lat", "")
            self.text_meta["ed_info"] = metadata.get("ed_info", "")
            self.text_meta["tok_length"] = metadata.get("tok_length", "")
            self.text_meta["tags"] = metadata.get("tags", "")
            self.author_meta["author_auto"] = metadata.get("author_from_uri", "")
            collection = re.match(r'^([A-Za-z]+)', metadata.get("Version", "")).group(0)

            if collection in collection_mappings:
                self.text_meta["collection"] = collection_mappings[collection]

            # Additional logic for title_lat
            title_lat = str(metadata.get("title_lat", ""))
            if " :: " in title_lat:
                parts = title_lat.split(" :: ")
                self.text_meta["title_lat"] = parts[0]
            else:
                self.text_meta["title_lat"] = title_lat

            # Additional logic for title_ar
            title_ar = str(metadata.get("title_ar", ""))
            if " :: " in title_ar:
                parts = title_ar.split(" :: ")
                self.text_meta["title_ar"] = parts[0]
            else:
                self.text_meta["title_ar"] = title_ar

            # Additional logic for author_lat_shuhra
            author_lat_shuhra = metadata.get("author_lat_shuhra", "")
            if not pd.isna(author_lat_shuhra):
                self.author_meta["author_lat_shuhra"] = author_lat_shuhra

            # Additional logic for author_lat_full_name
            author_lat_full_name = metadata.get("author_lat_full_name", "")
            if not pd.isna(author_lat_full_name):
                if not pd.isna(author_lat_shuhra):
                    self.author_meta["author_lat"] = f"{author_lat_shuhra}, {author_lat_full_name}"
                else:
                    self.author_meta["author_lat"] = author_lat_full_name

            # Additional logic for author_ar
            author_ar = str(metadata.get("author_ar", ""))
            if " :: " in author_ar:
                parts = author_ar.split(" :: ")
                self.author_meta["author_ar_shuhra"] = parts[0]
                self.author_meta["author_ar"] = self.name_parser.parse_arabic_name(parts[1])
            else:
                self.author_meta["author_ar"] = self.name_parser.parse_arabic_name(author_ar)

        else:
            print("Metadata not found for text_id:", text_id)

    def fetch_metadata(self, text_id):
        try:
            metadata_row = self.df[self.df["Version"] == text_id].iloc[0]
            metadata = metadata_row.to_dict()
            return metadata
        except Exception as e:
            print("Error fetching metadata:", e)
            return None
