from collections import namedtuple

ChineseRecognitionOnly = namedtuple('ChineseRecognitionOnly', 'simplified traditional pinyin zhuyin definition extra_definition words_with_same_pronunciation words_with_same_definition tags')
def word_to_ChineseRecognitionOnly(word, tags):
  'converts `ChineseWord` word to ChineseRecognitionOnly tuple'
  definition = '; '.join(word.english)
  tags = ' '.join(tags)
  traditional = '' if word.simplified == word.traditional else word.traditional
  return ChineseRecognitionOnly(word.simplified, traditional, word.pinyin, word.zhuyin, definition, '', '', '', tags)
