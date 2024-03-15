# Mutūn Pipeline

This is a pipeline developed to process OpenITI mARkdown files for import into the [mutun.io](www.mutun.io) corpus.
  
### Installation
  Clone the repo or download files and unzip.  
  Edit file directories in config.py  
  Run main.py
  
### Usage
  There are several stages in the pipeline
  1. Parse metadata header in raw OpenITI Markdown file and save as individual text metadata JSON and author metadata JSON.
  2. Preprocess raw OpenITI Markdown file to preserve structural annotations (paragraphs, headings, pages) with html tags. 
  4. Use OpenITI parser to provide clean the text of annotations.
  5. Apply additional cleaning of erroneous structural elements, leftover symbols, leftover annotations, and other issues.
  6. Paginate and parse the clean text with CAMeL tools Analyzer
  7. Output individual page-level JSON objects with full page text and token-level analysis

  This pipeline outputs individual JSON objects for auto metadata, text metadata, and individual pages. This output can easily be changed by editing the parse_text function in the text_parser module as well as the save_page_json function. Mutun.io uses an elasticsearch back end which is optimized for non-nested objects. This is why this pipeline produces page-level JSON objects, which are more perfomant for complex searching and producing corpus statistics and analytics.

### Example Outputs

  Text Metadata JSON Object in json\text_meta:
  ```
  0279Tirmidhi.MukhtasarShamailMuhammadiyya.Shamela0000700.json
  ```
  ```
  {
    "text_uri": "0360Tabarani.Awail.JK000862-ara1",
    "text_id": "JK000862",
    "title_ar": "الأوائل للطبراني",
    "title_lat": "NODATA",
    "author_id": "0360Tabarani",
    "ed_info": "محمد شكور بن محمود الحاجي أمرير :: بيروت :: 1403 :: مؤسسة الرسالة , دار الفرقان",
    "collection": "al-Jāmiʿ al-Kabīr",
    "tok_length": 5145,
    "page_count": 100,
    "volumes": "NODATA",
    "tags": "_HADITH :: _AJZA :: _TARAJIM :: _TABAQAT"
  }
  ```
  Author Metadata JSON Object in json\author_meta:
  ```
  0279Tirmidhi.MukhtasarShamailMuhammadiyya.Shamela0000700.json
  ```
  ```
  {
    "author_id": "0360Tabarani",
    "author_ar": "سليمان بن أحمد الطبراني أبو القاسم",
    "author_ar_shuhra": "الطبراني",
    "author_lat": "Tabarani",
    "author_lat_shuhra": "NODATA",
    "author_auto": "Tabarani",
    "au_death_hij": "360",
    "version": "JK000862"
  }
  ```
  Example Page JSON Object in json\text_content\0279Tirmidhi.MukhtasarShamailMuhammadiyya.Shamela0000700-ara1:
  ```
  Shamela0000700-01-22.json
  ```
  ```
  {
      "text_id": "MukhtasarShamailMuhammadiyya.Shamela0000700-ara",
      "author_id": "0279Tirmidhi",
      "volume_num": 1,
      "page_num": 22,
      "page_text": "<p>بالخاصة على العامة ولا يدخرعنهم شيئا </p><p>وكان من سيرته في جزء الأمة إيثار أهل الفضل بإذنه وقسمه على قدر فضلهم في الدين فمنهم ذو الحاجة ومنهم ذو الحاجتين ومنهم ذو الحوائج فيتشاغل بهم ويشغلهم فيما يصلحهم والأمة من مساءلتهم عنه </p><p>وإخبارهم بالذي ينبغي لهم ويقول: (ليبلغ الشاهد منكم الغائب وأبلغوني حاجة من لا يستطيع إبلاغها فإنه من أبلغ سلطانا حاجة من لا يستطيع إبلاغها ثبت الله قدميه يوم القيامة) </p><p>لايذكر عنده إلا ذلك ولا يقبل من أحد غيره يدخلون روادا ولا يفترقون إلا عن ذواق ويخرجون أدلة يعني على الخير </p><p>قال: فسألته عن مخرجه كيف كان يصنع فيه؟ قال: </p><p>[22] </p>",
      "chapter_headings": [],
      "order": 19,
      "tokens": [
          {
              "index": 1,
              "tok": "بالخاصه",
              "lem": "خاصّ",
              "rt": "خ.ص.ص",
              "pos": "adj",
          },
          {
              "index": 2,
              "tok": "علي",
              "lem": "عَلَى",
              "rt": "ع.ل.#",
              "pos": "prep",
          },
          {
              "index": 3,
              "tok": "العامه",
              "lem": "عامّ",
              "rt": "ع.م.م",
              "pos": "adj",
          },
          ...
  ```
  You can adjust what morphological features you want to include in camel_analyzer module with reference in the [CAMeL Lab Docs](https://camel-tools.readthedocs.io/en/latest/reference/camel_morphology_features.html?highlight=diac)
### Additional Tool

There is also a json_meta_csv module that will convert all JSON objects in either of the metadata folders into a single csv file.
###  Contributing
[CAMeL Lab](https://github.com/CAMeL-Lab/)  
[OpenITI](https://github.com/OpenITI)
###  License
This pipeline is available under the MIT License. See [LICENSE](https://github.com/ammusto/mutun_pipeline/blob/main/LICENSE) file for more info
