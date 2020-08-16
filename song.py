from constants import *
from buttons import SequencerButtons
import yaml

class Song:
  def __init__(self):
    self.patterns = {}

  @staticmethod
  def name(num, version):
    return "/home/pi/src/sequencer/songs/chopogy-%d-v%d" % (num, version)

def save(midi_h, sequencers, song_num):

  # generate sample pack ie...
  # "/home/pi/chopogy/packs/<song_num>/chan.pack.yaml"
  cmd = PROGRAM_APP_VALUE[PROGRAM_SAVE_SONG]
  midi_h.controller_change(cmd, song_num)

  # dump to yaml
  song = Song()
  for _, seq in sequencers.items():
    # add each pattern
    song.patterns[seq.channel] = seq.pattern

  # save
  song_name = Song.name(song_num, midi_h.channel)
  stream = open(song_name, 'w')
  yaml.dump(song, stream)
  print("Saved: ", song_name)

def load(midi_h, trellis, song_num):

  # load sample pack ie...
  # "/home/pi/chopogy/packs/<song_num>/chan.pack.yaml"
  cmd = PROGRAM_APP_VALUE[PROGRAM_LOAD_SONG]
  midi_h.controller_change(cmd, song_num)

  # load song from yaml
  song_name = Song.name(song_num, midi_h.channel)
  stream = open(song_name, 'r')
  song = yaml.load(stream, Loader=yaml.Loader)

  # return patterns for sequencers
  sequencers = {}
  for channel, pattern in song.patterns.items():
    seq = SequencerButtons(trellis, midi_h, channel)
    seq.pattern = pattern
    sequencers[channel] = seq
    print("Loaded Sequencer: ", channel, pattern)

  return sequencers
