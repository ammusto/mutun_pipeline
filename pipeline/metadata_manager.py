import re

from pipeline.utility import Utility
from pipeline.name_parser import NameParser


class MetaDataManager:
    def __init__(self):
        self.author_meta = {
            "author_id": "", "author_ar": "", "author_raw": "", "author_translit": "",
            "author_auto": "", "au_born_hij": "", "au_death_hij": "", "au_death_greg": ""
        }
        self.text_meta = {
            "text_id": "", "author_id": "", "text_version": "", "title_ar": "", "title_translit": "",
            "title_auto": "", "title_translate": "", "bibliography": "", "page_count": "", "subject": "",
            "editor": "", "edition": "", "volumes": "", "publisher": "", "pub_date": "", "collection": "",
            "transcriber": "", "translator": "", "digitization": "", "ms_source": "", "tags": "",
            "url": ""
        }

    # parse metadata headers from: shamela, JK, shia, PV, and filaha corpora

    def parse_ssjpf(self, text):
        for line in text:
            line = line.strip()
            if line == '#META#Header#End#':
                break
            if "::" in line:
                tag, value = line.split("::", 1)
                value = value.strip()
                if "AuthorNAME" in tag:
                    self.author_meta["author_raw"] = value
                    self.author_meta["author_ar"] = NameParser.parse_arabic_name(value).replace("،", "")
                elif "AuthorBORN" in tag:
                    self.author_meta["au_born_hij"] = Utility.format_date(value, "author")
                elif "AuthorDIED" in tag:
                    if self.author_meta["au_death_hij"] in ("NODATA", ""):
                        self.author_meta["au_death_hij"] = Utility.format_date(value, "author")
                elif "BookTITLE" in tag:
                    self.text_meta["title_ar"] = Utility.remove_paren(value)
                elif "BookSUBJ" in tag:
                    subjects = [subj.strip() for subj in value.split('::')]
                    self.text_meta["subject"] = ', '.join(subjects)
                elif "BookVOLS" in tag:
                    self.text_meta["volumes"] = Utility.remove_paren(value)
                elif "LibREADONLINE" in tag:
                    self.text_meta["url"] = value
                elif "LibURL" in tag:
                    if value != "NODATA":
                        self.text_meta["url"] = value
                elif "EdEDITOR" in tag:
                    value = value.replace(" (ع)", "")
                    if ":" in value:
                        value = value.split(": ")[1]
                    self.text_meta["editor"] = ", ".join(part.strip() for part in re.split(r'\bو', value))
                elif "EdPUBLISHER" in tag:
                    self.text_meta["publisher"] = (lambda parts: ": ".join(parts[::-1]) if len(parts) == 2 else value)(
                        re.split(r' - |، ', value))
                elif "EdYEAR" in tag and self.text_meta["pub_date"] == "":
                    self.text_meta["pub_date"] = Utility.format_date(value, "pub")
                elif "EdPLACE" in tag:
                    if value != "NODATA":
                        value = value.strip(".")
                        self.text_meta["publisher"] = f"{value}: {self.text_meta['publisher']}"
                elif "EdNUMBER" in tag:
                    if value == "NODATA":
                        pass
                    elif not re.search(r'\d', value):
                        self.text_meta["edition"] = value
                    else:
                        self.text_meta["pub_date"] = Utility.format_date(value, "pub")

    # parse metadata headers from: hindawi, tafsir, and LAL
    def parse_htl(self, text):
        for line in text:
            line = line.strip()
            if line == '#META#Header#End#':
                break
            if ":" in line:
                tag, value = line.split(":", 1)
                value = value.strip()
                if "Author" in tag:
                    self.author_meta["author_ar"] = value
                elif "المؤلف" in tag:
                    self.author_meta["author_ar"] = value
                elif "Title" in tag:
                    self.text_meta["title_ar"] = value
                elif "(EN)" in tag:
                    self.text_meta["title_translate"] = value
                elif "Editor" in tag:
                    self.text_meta["editor"] = value
                elif "Publisher" in tag:
                    self.text_meta["publisher"] = value
                elif "Place of publication" in tag:
                    self.text_meta["publisher"] = f"{value}, {self.text_meta['publisher']}"
                elif "Tafsir" in tag:
                    self.text_meta["subject"] = value
                elif "Witness" in tag:
                    value = value.replace("الأصل: ", "")
                    self.text_meta["ms_source"] = value

    # parse metadata headers from: meshkat, rafed, shamidabiyya, shamAY, sham19, zaydiyya, and masaha corpora

    def parse_mrssszm(self, text):
        for line in text:
            line = line.strip()
            if line == '#META#Header#End#':
                break
            if ":" in line:
                tag, value = line.split(":", 1)
                value = value.strip()
                if "title" in tag or "bk" in tag and "ord" not in tag and "id" not in tag:
                    self.text_meta["title_ar"] = value.split(" - ")[0]
                elif "المؤلف" in tag:
                    self.author_meta["author_raw"] = value.replace(" (ع)", "")
                    value = re.sub(r'\(.*?\)', '', value)
                    self.author_meta["author_ar"] = NameParser.parse_arabic_name(value).replace("،", "")
                elif "auth" in tag and "inf" not in tag and "oauth" not in tag:
                    if self.author_meta["author_raw"] == "" and self.author_meta["author_ar"] == "":
                        self.author_meta["author_raw"] = value.replace(" (ع)", "")
                        value = re.sub(r'\(.*?\)', '', value)
                        self.author_meta["author_ar"] = NameParser.parse_arabic_name(value).replace("،", "")
                elif "lng" in tag:
                    self.author_meta["author_raw"] = value
                elif "المواضيع" in tag or "cat" in tag or "موضوع" in tag:
                    self.text_meta["subject"] = value
                elif "محقق" in tag:
                    self.text_meta["editor"] = value.replace("\t", "")
                elif "url" in tag:
                    self.text_meta["url"] = value
                elif "عدد" in tag and "الصفحات" not in tag:
                    self.text_meta["volumes"] = value
                elif "ناشر" in tag:
                    self.text_meta["publisher"] = value
                    value = value.split()
                    if value[-1].isdigit():
                        self.text_meta["pub_date"] = value[-1]
                elif "مصدر المخطوط" in tag:
                    self.text_meta["ms_source"] = value
                elif "مكان" in tag:
                    self.text_meta["publisher"] = f"{value}, {self.text_meta['publisher']}"
                elif "تاريخ" in tag:
                    self.text_meta["pub_date"] = re.sub(r'[^0-9]', '', value)
                elif "أعده للشاملة" in tag:
                    self.text_meta["transcriber"] = value
                elif "الطبعة" in tag:
                    self.text_meta["pub_date"] = Utility.format_date(value, "pub")

    # parse metadata headers from: GRAR, PAL, ALcorpus, JT, and MMS

    def parse_gpajm(self, text):
        for line in text:
            line = line.strip()
            if line == '#META#Header#End#':
                break
            if ":" in line:
                tag, value = line.split(":", 1)
                value = value.strip()
                if "Author" in tag or "author" in tag and "id" not in tag and "latin" not in tag:
                    self.author_meta["author_translit"] = value
                elif "title_short" in tag:
                    self.text_meta["title_translate"] = value
                elif "title" in tag or "Title" in tag and "short" not in tag:
                    self.text_meta["title_translit"] = value
                elif "ed_info" in tag:
                    self.text_meta["bibliography"] = value
                elif "transcriber" in tag:
                    self.text_meta["transcriber"] = value
                elif "responsibility" in tag:
                    value = value.replace("transcribed by ", "")
                    self.text_meta["transcriber"] = value
                elif "url" in tag and "transcription" not in tag:
                    self.text_meta["url"] = value
                elif "url" in tag and "transcription" in tag:
                    self.text_meta["url"] = f"ptolemaeus.badw.de{value}"
                elif "Editor" in tag:
                    self.text_meta["editor"] = value
                elif "Publisher" in tag:
                    self.text_meta["publisher"] = value
                elif "Date of publication" in tag:
                    self.text_meta["pub_date"] = value
                elif "Place of publication" in tag:
                    self.text_meta["publisher"] = f"{value}, {self.text_meta['publisher']}"
                elif "digitization" in tag:
                    self.text_meta["digitization"] = value
                elif "source" in tag:
                    self.text_meta["ms_source"] = value
                elif "Volumes" in tag:
                    self.text_meta["volumes"] = value
