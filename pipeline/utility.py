import re

class Utility:
    @staticmethod
    def format_date(input_str, kind):
        if kind == "pub":
            matches = re.findall(r'\b\d{4}(?=\D|$)', input_str)
        elif kind == "author":
            matches = re.findall(r'\b\d{3,}\D?', input_str)
        numbers = [re.sub(r'\D', '', match) for match in matches]
        if len(numbers) == 1:
            return numbers[0]
        elif len(numbers) == 2:
            return '/'.join(sorted(numbers))
        else:
            return "NODATA"

    @staticmethod
    def remove_paren(string):
        return re.sub(r"\(.*?\)", "", string).strip()

    @staticmethod
    def fill_empty_nodata(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = Utility.fill_empty_nodata(value)
        elif isinstance(obj, list):
            return [Utility.fill_empty_nodata(item) for item in obj]
        elif obj == "" or obj == "لا يوجد":
            return "NODATA"
        return obj
