from braid import *
from rtmidi.midiconstants import *

class MidiHandler:
  def __init__(self, ch=1):
    midi_in.midi.set_callback(self.receive_message)
    self.last_note = None
    self.channel = ch
    # just starting at value that aligns with arturia keyboard
    self.note_offset = 20 

  def receive_message(self, event, data = None):
    if len(event):
      message, ts = event
      # save if message was note with velocity
      if len(message) == 3 and message[2] > 0:
        self.last_note = message
        # TODO: remember rm this when offset is removed
        # this is set because last note doesn't correspond
        self.last_note[1] = self.last_note[1] - self.note_offset

  def channel_message(self, command, *data, ch=None):
      """Send a MIDI channel mode message."""
      command = (command & 0xf0) | ((ch if ch else self.channel) - 1 & 0xf)
      msg = [command] + [value & 0x7f for value in data]
      midi_out.midi.send_message(msg)
  
  def note_off(self, note, velocity=0, ch=None):
      """Send a 'Note Off' message."""
      self.channel_message(NOTE_OFF, note + self.note_offset, velocity, ch=ch)
  
  def note_on(self, note, velocity=127, ch=None):
      """Send a 'Note On' message."""
      self.channel_message(NOTE_ON, note + self.note_offset, velocity, ch=ch)
  
  def program_change(self, program, ch=None):
    """Send a 'Program Change' message."""
    self.channel_message(PROGRAM_CHANGE, program, ch=ch)

  def controller_change(self, controller, value, ch=None):
    """Send a 'Controller Change' message."""
    self.channel_message(CONTROLLER_CHANGE, controller, value, ch=ch)

  def reset_offset(self):
    self.note_offset = 20 
  def prev_offset(self):
    self.note_offset = self.note_offset - 16
    if self.note_offset < 0:
       self.note_offset = 0
  def next_offset(self):
    self.note_offset = self.note_offset + 16
    if self.note_offset > 88:
      self.note_offset = 72 

def NoteOn(value, velocity=0xFF):
  return [NOTE_ON, value, velocity]
def NoteOff(value, velocity=0xFF):
  return [NOTE_OFF, value, velocity]
