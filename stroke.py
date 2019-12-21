import requests
import os

def get_stroke(hanzi):
  # Add a space between images because it looks nicer
  return ' '.join(map(get_stroke_single, hanzi))

def get_stroke_single(hanzi):
  if not os.path.exists('content/'):
    os.mkdir('content/')

  gif_loc = f'content/{hanzi}.gif'
  if not os.path.exists(gif_loc):
    hanzi_id = str(ord(hanzi))
    response = requests.get(f'https://www.mdbg.net/chinese/rsc/img/stroke_anim/{hanzi_id}.gif')

    if not (response.ok and response.content):
      print(u"Unable to fetch stroke for {hanzi}.")
      return ""

    open(gif_loc, 'wb').write(response.content)

  # The gif should be moved into Anki's collections.media folder,
  # where it may be referenced within the note simply by filename, not location
  return f'<img src="{hanzi}.gif">'
