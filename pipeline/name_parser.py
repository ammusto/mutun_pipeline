import re


# parse and shorten arabic names from raw name to parsed shortened name
class NameParser:
    def parse_arabic_name(self, raw_name):
        if not isinstance(raw_name, str):
            return "NODATA"  # Return the input as it is if it's not a string
        substitutions = [
            (r'\(م\)', ''),
            (r'\(?(المتوفى).*', ''),
            (r'\.', ''),
            (r':+', '،'),
            (r'،+', '،')
        ]

        name_no_date = raw_name
        for pattern, replacement in substitutions:
            name_no_date = re.sub(pattern, replacement, name_no_date)

        name_no_date = name_no_date.strip()
        removed_laqab = name_no_date.split(" أو ", 1)[-1]
        parts = removed_laqab.split("،")
        parts = [part for part in (p.strip() for p in parts) if part]
        if len(parts) > 1 and parts[-1].split()[-1].endswith("ي"):
            removed_added = parts[0] + "،" + parts[-1]
        else:
            removed_added = parts[0]
        name_parts = re.split(r' بن ', removed_added)
        name_parts = [part.strip() for part in name_parts]
        if len(name_parts) > 3:
            if name_parts[-1].startswith('ابن'):
                name_parts = name_parts[:2] + [' بن '.join(name_parts[2:])]
        if len(name_parts) > 2:
            last_part_words = name_parts[-1].split()
            last_part = " ".join(last_part_words[2:]) if last_part_words[0] in ["عبد", "أبي"] else " ".join(
                last_part_words[1:])
        else:
            last_part = ""
        parsed_name = " بن ".join(name_parts[:2]) + " " + last_part if " بن " in removed_added else removed_added
        parsed_name = parsed_name.rsplit("،", 1)[0] if "،" in parsed_name else parsed_name
        return parsed_name.strip()
