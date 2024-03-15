import regex
import re

from camel_tools.tokenizers.word import simple_word_tokenize
from camel_tools.utils.normalize import normalize_unicode, normalize_alef_maksura_ar, normalize_alef_ar, \
    normalize_teh_marbuta_ar
from camel_tools.utils.charmap import CharMapper
from camel_tools.utils.charsets import UNICODE_PUNCT_SYMBOL_CHARSET
from camel_tools.utils.dediac import dediac_ar


class TextAnalyzer:
    def __init__(self, text, disambiguator):
        self.arclean = CharMapper.builtin_mapper('arclean')  # create a character mapper for arabic cleaning
        self.disambiguator = disambiguator  # initialize the disambiguator
        self.text = text  # store the input text
        self.analysis_result = self._analyze()  # analyze the text upon initialization

    # private methods for text preprocessing
    def _strip_html(self, text):
        # remove HTML tags from the text using regular expressions
        html_tags_pattern = re.compile(r'<[^>]+>')
        stripped_text = html_tags_pattern.sub('', text)
        return stripped_text

    def _strip_punct(self, text):
        # remove punctuation symbols from the text
        stripped_text = ''.join(c for c in text if c not in UNICODE_PUNCT_SYMBOL_CHARSET)
        return stripped_text

    def _strip_latin(self, text):
        # remove latin characters from the text using regular expressions
        stripped_text = regex.sub(r'[\p{Latin}]', '', text)
        return stripped_text

    def _strip_num(self, text):
        # remove digits from the text
        stripped_text = ''.join(c for c in text if not c.isdigit())
        return stripped_text

    def _preprocess(self, text):
        # preprocess the text by applying various cleaning and normalization steps
        text = self.arclean(text)  # clean Arabic characters
        text = self._strip_html(text)  # remove HTML tags
        text = self._strip_punct(text)  # remove punctuation
        text = self._strip_latin(text)  # remove Latin characters
        text = self._strip_num(text)  # remove digits
        text = normalize_unicode(text)  # normalize Unicode characters
        text = normalize_alef_ar(text)  # normalize Arabic alif characters
        text = normalize_alef_maksura_ar(text)  # normalize alif maksura characters
        text = normalize_teh_marbuta_ar(text)  # normalize ta marbuta characters
        return text

    def _analyze(self):
        # perform text analysis
        preprocessed_text = self._preprocess(self.text)  # preprocess the input text
        tokens = simple_word_tokenize(preprocessed_text)  # tokenize the preprocessed text
        disambig = self.disambiguator.disambiguate(tokens)  # disambiguate tokenized words

        # prepare the analysis based on certain morphological features
        output = []
        for i, d in enumerate(disambig, start=1):
            analysis_dict = {
                "index": i,
                "tok": d.word,  # Token
                "lem": next((dediac_ar(analysis.analysis['lex']) for analysis in d.analyses), None),  # lemma
                "rt": next((analysis.analysis['root'] for analysis in d.analyses), None),  # root
                "pos": next((analysis.analysis['pos'] for analysis in d.analyses), None),  # part-of-speech
            }
            output.append(analysis_dict)  # add analysis dictionary to the output list

        return output

    def get_analysis_result(self):
        return self.analysis_result
