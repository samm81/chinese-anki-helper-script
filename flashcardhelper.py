import cmd
import argparse
import csv
from dragonmapper import hanzi, transcriptions
from opencc import OpenCC
from cccedict import find_words
from functools import wraps
from enum import Enum
from flashcardschemas import ChineseRecognitionOnly, word_to_ChineseRecognitionOnly
from stroke import get_stroke

s2t = OpenCC('s2t')
t2s = OpenCC('t2s')

State = Enum('State', 'BEGIN PICK_WORD PICK_ENGLISH PICKED')

class FlashcardHelper(cmd.Cmd):
  filename = 'cards.csv'
  intro = 'Welcome to flashcard helper. Type help or ? to list commands\n'
  prompt = '入 '

  words = []
  word = None
  choice = None
  state = State.BEGIN
  filemode = False

  def transition_to(self, to_state):
    if to_state is State.BEGIN:
      self.words = []
      self.state = to_state
    elif to_state is State.PICK_WORD:
      self.state = to_state
    elif to_state is State.PICK_ENGLISH:
      self.state = to_state
    elif to_state is State.PICKED:
      if self.state is State.PICK_WORD:
        self.word = self.words[self.choice]
        return self.handle_word()
      elif self.state is State.PICK_ENGLISH:
        return self.handle_english()

  def transitions_to(to_state):
    'convenience decorator for functions that only transition to one state'
    def transition_decorator(func):
      @wraps(func)
      def wrapper(self, *args, **kwargs):
        retval = func(self, *args, **kwargs)
        self.transition_to(to_state)
        return retval
      return wrapper
    return transition_decorator

  def handle_word(self, word_to_flashcard=word_to_ChineseRecognitionOnly):
    if len(self.word.english) is 1:
      flashcard = word_to_flashcard(self.word, [])
      retval = self.save_to_file(flashcard)
      self.transition_to(State.BEGIN)
      return retval
    else:
      print('which definitions should go in the main definition?')
      self.display_options(self.word.english, multiple=True)
      self.transition_to(State.PICK_ENGLISH)

  @transitions_to(State.BEGIN)
  def handle_english(self):
    primaries = [ english for i, english in enumerate(self.word.english) if i in self.choice ]
    secondaries = [ english for i, english in enumerate(self.word.english) if i not in self.choice ]
    definition = '; '.join(primaries)
    extra_definition = '; '.join(secondaries)
    flashcard = ChineseRecognitionOnly(self.word.simplified, self.word.traditional, self.word.pinyin, self.word.zhuyin, definition, extra_definition, '', '', '')
    return self.save_to_file(flashcard)

  def display_options(self, optionstrings, multiple=False):
    print('\n'.join('{}) {}'.format(i, optionstring) for i, optionstring in enumerate(optionstrings)))
    if multiple:
      print('type `pick [num] ([num] [num]) to pick option(s), or type any other command')
    else:
      print('type `pick [num]` to pick an option, or type any other command')

  def save_to_file(self, flashcard, filename=filename):
    confirm = input(f'saving {flashcard} to file {filename}, looks ok ([Y]n) ? ')
    if confirm.strip().lower() in ['n', 'no']:
      print('not saved.')
    else:
      with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(flashcard)
      print('saved!')
    # if we're operating over a file our job for this word is done and we wanna return control to our file loop!
    if self.filemode:
      return True

  def do_find(self, arg):
    'find a chinese character or phrase: find ni3hao'
    if not(transcriptions.is_pinyin(arg) or hanzi.is_simplified(arg) or hanzi.is_traditional(arg)):
      print('input is not well formed pinyin or well formed Chinese characters')
      return # don't transition state
    words = find_words(arg)
    if len(words) is 0:
      print('could not find character or phrase')
      return # don't transition state
    self.words = words
    if len(words) is 1 and self.filemode:
      self.choice = 0
      self.state = State.PICK_WORD
      return self.transition_to(State.PICKED)
    else:
      self.display_options('{}\t{}\t{}\t{}\t{}'.format(*word) for word in words)
      self.transition_to(State.PICK_WORD)

  # TODO pick all
  def do_pick(self, arg):
    if not (self.state is State.PICK_WORD or self.state is State.PICK_ENGLISH):
      print('no options to pick from right now!')
      return # don't transition state
    choices = list(map(int, arg.split()))
    if len(choices) is 0:
      print('must chose an option!')
      return # don't transition state
    elif self.state is State.PICK_WORD and len(choices) is 1:
      self.choice = choices[0]
    elif self.state is State.PICK_WORD and len(choices) > 1:
      print('can only chose one option!')
      return # don't transition state
    else:
      self.choice = choices
    return self.transition_to(State.PICKED)

  def do_make(self, arg):
    'make a custom flashcard: make 什么什么'
    if not hanzi.has_chinese(arg):
      print('input is not well formed chinese characters')
      return # don't transition state
    simplified = t2s.convert(arg)
    traditional = s2t.convert(arg)
    pinyin = hanzi.to_pinyin(arg)
    zhuyin = hanzi.to_zhuyin(arg)
    english = input('english definition: ')
    simplified_stroke = get_stroke(simplified)
    traditional_stroke = get_stroke(traditional)
    self.save_to_file(ChineseRecognitionOnly(simplified, traditional, pinyin, zhuyin, simplified_stroke, traditional_stroke, english, '', '', '', ''))
    self.transition_to(State.BEGIN)

  def do_EOF(self, arg):
    'exit'
    print('exiting.')
    return True

  def do_exit(self, arg):
    'exit'
    print('exiting.')
    return True

  def register_filemode(self):
    'used when reading a set of words from a file so that the cmd knows to finish after saving a card'
    self.filemode = True

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Command line helper for making Chinese Anki flashcards')
  parser.add_argument('file', nargs='?', type=argparse.FileType('r', encoding='utf-8'), help='newline separated file of words to add')
  args = parser.parse_args()

  helper_cmd = FlashcardHelper()
  if not args.file:
    helper_cmd.cmdloop()
  else:
    print(f'loading {args.file.name}...')
    words = args.file.read().splitlines()
    helper_cmd.register_filemode()
    for i, word in enumerate(words):
      print(f'looking up {word} (word {i} of {len(words)})')
      helper_cmd.onecmd(f'find {word}')
      helper_cmd.cmdloop(intro='')
