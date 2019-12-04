import re
from collections import namedtuple
from dragonmapper import hanzi, transcriptions

# monkeypatch dragonmapper to handle english syllables
def pinyin_or_english_syllable_to_zhuyin(s):
  pinyin_syllable, tone = transcriptions._parse_pinyin_syllable(s)
  try:
    zhuyin_syllable = transcriptions._PINYIN_MAP[pinyin_syllable.lower()]['Zhuyin']
  except KeyError:
    return pinyin_syllable
  return zhuyin_syllable + transcriptions._ZHUYIN_TONES[tone]
transcriptions.pinyin_syllable_to_zhuyin = pinyin_or_english_syllable_to_zhuyin

# used internally, no point in storing fields we can calculate
_ChineseWord = namedtuple('ChineseWord', ['simplified', 'traditional', 'numbered_pinyin', 'english'])
ChineseWord = namedtuple('ChineseWord', ['simplified', 'traditional', 'pinyin', 'zhuyin', 'english'])

def _get_and_load_cedict_file(url='https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz', filename='cedict.txt'):
  try:
    with open(filename) as cedictfile:
      yield from cedictfile
  except FileNotFoundError:
    # TODO fix
    # https://docs.python.org/3.6/library/gzip.html
    # https://docs.python.org/3.6/library/urllib.request.html#urllib.request.urlopen
    # https://docs.python.org/3.6/library/shutil.html#shutil.copyfileobj
    # https://stackoverflow.com/questions/7243750/download-file-from-web-in-python-3
    import urllib.request
    import gzip
    import shutil
    with urllib.request.urlopen(url) as response:
      with gzip.GzipFile(fileobj=response) as uncompressed, open(filename, 'w') as outfile:
        shutil.copyfileobj(uncompressed, outfile)
    with open(filename) as cedictfile:
      yield from cedictfile

def _parse_cedict_file(cedict_file_it):
  return (_parse_cedict_entry(entry) for entry in cedict_file_it if entry[0] != '#')

ENTRY_RE = re.compile(r'^(?P<traditional>\S*)\s*(?P<simplified>\S*)\s*\[(?P<numbered_pinyin>.*?)\]\s*(/(?P<englishes>.*))*/$')
def _parse_cedict_entry(entry):
  m = ENTRY_RE.match(entry)
  simplified, traditional, numbered_pinyin, englishes = (m.group(prop) for prop in [ 'simplified', 'traditional', 'numbered_pinyin', 'englishes' ])
  english = englishes.split('/')
  return _ChineseWord(simplified, traditional, numbered_pinyin, english)

from itertools import islice
words_iter = _parse_cedict_file(_get_and_load_cedict_file())
#words_iter = islice(words_iter, 0, 1000)
WORDS = list(words_iter)

def _numbered_pinyin_match(npinyin1, npinyin2):
  ind1 = 0
  ind2 = 0
  while ind1 < len(npinyin1) or ind2 < len(npinyin2):
    if ind1 >= len(npinyin1):
      if npinyin2[ind2].isdigit() or npinyin2[ind2] is ' ':
        ind2 += 1
        continue
      return False
    if ind2 >= len(npinyin2):
      if npinyin1[ind1].isdigit() or npinyin1[ind1] is ' ':
        ind1 += 1
        continue
      return False
    if npinyin1[ind1] == npinyin2[ind2]:
      ind1, ind2 = ind1 + 1, ind2 + 1
      continue
    if npinyin1[ind1] == ' ':
      ind1 += 1
      continue
    if npinyin2[ind2] == ' ':
      ind2 += 1
      continue
    if npinyin1[ind1].isdigit() and not npinyin2[ind2].isdigit():
      ind1 += 1
      continue
    if npinyin2[ind2].isdigit() and not npinyin1[ind1].isdigit():
      ind2 += 1
      continue
    return False
  return True

def hydrate_word(_word):
  accented_pinyin = transcriptions.numbered_to_accented(_word.numbered_pinyin)
  zhuyin = transcriptions.pinyin_to_zhuyin(_word.numbered_pinyin)
  return ChineseWord(_word.simplified, _word.traditional, accented_pinyin, zhuyin, _word.english)

def hydrate_words(finder):
  def hydrated_finder(*args, **kwargs):
    return [ hydrate_word(word) for word in finder(*args, **kwargs) ]
  return hydrated_finder

@hydrate_words
def find_words_by_pinyin(pinyin):
  # TODO this line changes "liu" to "liu5"
  #pinyin = transcriptions.accented_to_numbered(pinyin)  # just in case
  return [ word for word in WORDS if _numbered_pinyin_match(word.numbered_pinyin, pinyin) ]

@hydrate_words
def find_words_by_hanzi(hz):
  return [ word for word in WORDS if word.simplified == hz or word.traditional == hz ]

# TODO zhuyin support
def find_words(s):
  '''
  figures out if s is simplified, traditional, numbered pinyin, accented
  pinyin, or zhuyin and looks up in dictionary
  '''
  if transcriptions.is_pinyin(s):
    return find_words_by_pinyin(s)
  if hanzi.is_simplified(s) or hanzi.is_traditional(s):
    return find_words_by_hanzi(s)

  raise NotImplementedException()

if __name__ == '__main__':
  print('---')
  print(find_words_by_pinyin('liu4'))
  print('---')
  print(find_words_by_pinyin('liu'))
  print('---')
  print(find_words_by_pinyin('ni3hao3'))
  print('---')
  print(find_words_by_pinyin('ni3 hao3'))
  print('---')
  print(find_words_by_pinyin('ni3 hao3'))
