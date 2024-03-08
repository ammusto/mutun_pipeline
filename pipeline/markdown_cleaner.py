import oimdp
import os
import re

path = os.getcwd()
fileNames = []
rawdata_path = os.path.join(path, 'rawdata')
clean_path = os.path.join(path, 'clean_test')


def reg_replace(text, replacements):
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    return text


# preprocessing to preserve structural elements before openITI cleaner

def replace_chapter_headings(text):
    # replace chapter headings
    text = re.sub(r'###\s*\|+\s*(.*?)(?=P|$)', r'~~<h1>\1</h1>', text, flags=re.MULTILINE)
    # fix erroneous annotations
    text = re.sub(r'PageVPP', r'PageV01P', text, flags=re.MULTILINE)
    text = re.sub(r'PageV(\D)', r'PageV01P000\1', text, flags=re.MULTILINE)
    text = re.sub(r'#\d{1,}#', r'', text, flags=re.MULTILINE)
    text = re.sub(r'(PageV\d+P) (\d+)', r'\1\2', text, flags=re.MULTILINE)
    text = re.sub(r'\n (PageV\d+P\d+)', r'\n\1', text, flags=re.MULTILINE)
    text = re.sub(r'^# (?!PageV\d+P\d+)(.*)', r'~~<p>\1', text, flags=re.MULTILINE)
    # replace pagination with unique substitution characters for text_parser
    text = re.sub(r'PageV(\d+)P(\d+)', r'~~a11b\g<1>a11b\2', text, flags=re.MULTILINE)

    return text


# list of replacements for leftover annotations and extraneous characters not removed by openITI cleaner

replacements = {
    '\\n': ' ',
    'CHECK|AUTO|=|¬|_|^</p>|@\\D{,2}@|@\\D{1,}\\d{1,}\\s': '',
    '(a11b\\d{2}a11b\\d{3})': '\\1\\n',
    '\\n+': '\\n',
    '[ ]+': ' ',
    '<p>': '</p><p>',
    '<p><h1>': '<h1>',
    '</h1></p>': '</h1>',
    '(?<!</p>)(?=(a11b\\d{2}a11b\\d{3}))': '</p>',
    '^': '<p>',
    '<p><p>': '<p>',
    '<p> <p>': '<p>',
    '(?<=.)<h1>': '</p><h1>',
    '</h1>(?!(,\\d+|<p>))': '</h1><p>',
    '<p> </p>': '',
    '<p></p>': '',
    '\\n<p> $': '',
    '-+NO PAGE NO-+': 'a11b00a11b000'

}


# chunk texts that have no pages into 1800 character segments and paginate


def chunk_and_page(input_text):
    if re.search(r'a11b\d{2}a11b\d{3,}', input_text):
        return (input_text)
    # define a regular expression to match </p> and <p>
    pattern = re.compile(r'(</p>|<p>.*?</p>|<h1>.*?</h1>)', re.DOTALL)

    # split the input text into chunks of up to 300 characters
    chunks = []
    current_chunk = ""
    current_length = 0

    for match in pattern.finditer(input_text):
        part = match.group(0)

        # calculate the length of the content (excluding tags)
        content_length = len(re.sub(r'<[^>]+>', '', part))

        # check if adding the content to the current chunk would exceed 1800 characters
        if current_length + content_length <= 1800:
            current_chunk += part
            current_length += content_length
        else:
            # save the current chunk and start a new one
            chunks.append(current_chunk)
            current_chunk = part
            current_length = content_length

    # add the last chunk to the list
    if current_chunk:
        chunks.append(current_chunk)

    # number the chunks as requested
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            result.append(f"{chunk}a11b01a11b001\n")
        else:
            result.append(f"{chunk}a11b01a11b{str(i + 1).zfill(3)}\n")

    return "".join(result)


def clean_text(text):
    text = replace_chapter_headings(text)
    oi_parsed = oimdp.parse(text)
    oi_clean = oi_parsed.get_clean_text()
    mutun_clean = chunk_and_page(reg_replace(oi_clean, replacements))
    return mutun_clean
