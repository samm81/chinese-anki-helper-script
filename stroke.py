import requests
import re
import os
import time

def get_stroke(hanzi):
  return '&nbsp;'.join(map(get_stroke_single, hanzi))

def get_stroke_single(hanzi):
  if not os.path.exists('content/'):
    os.mkdir('content/')

  hanzi_id = str(ord(hanzi))
  gif_loc = 'content/' + hanzi_id + '.gif'

  if not os.path.exists(gif_loc):
    response = requests.get('https://www.mdbg.net/chinese/rsc/img/stroke_anim/{}.gif'.format(hanzi_id))

    if not response.ok and response.content:
      print(u"Unable to fetch stroke for {}, trying again...".format(hanzi))
      return ""

    open(gif_loc, 'wb').write(response.content)

  # The gif should be moved into Anki's collections.media folder,
  # where it may be referenced within the note simply by filename, not location
  return '<img src="' + hanzi_id + '.gif">'
