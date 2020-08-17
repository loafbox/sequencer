import time
from adafruit_trellis import Trellis
from rtmidi.midiconstants import *
from constants import *
from midi_handler import NoteOn

class ButtonState:
  def __init__(self):
    self.just_pressed = set()
    self.released = set()
    self.off_buttons = set()
    self.on_buttons = set()
    self.alt_pressed = False
    self.knob_controller = CHANGE_RATE

  def set_buttons(self, trellis):
    self.just_pressed, self.released = trellis.read_buttons()
    # remove any elements in just pressed and on buttons
    self.off_buttons = self.on_buttons.intersection(self.just_pressed)

  def get_buttons(self):
    return self.just_pressed, self.released, self.off_buttons, self.on_buttons

  def did_press_button(self):
    return len(self.just_pressed)

  def last_pressed_button(self):
    return self.did_press_button and self.just_pressed[0] or -1

  def reset_buttons(self):
    self.just_pressed = set()
    self.released = set()
    self.off_buttons = set()
    self.on_buttons = set()


class ControllerButtons:
  def __init__(self, midi_h):
    self.active = True
    self.midi_h = midi_h
    self.save_pending = False
    self.load_pending = False

  def update(self, state, knob):

    just_pressed, released, _, _ = state.get_buttons()

    # handle control button presses
    for button in just_pressed:

      # alt_pressed modifier
      if CONTROLS[button] == FUNCTION:
        state.alt_pressed = True

      # program Change
      if CONTROLS[button] == PROGRAM_CHANGE:

        # alt_pressed on program changes moves to next range
        if state.alt_pressed:
          button = button + 4
        self.set_program(button, state.alt_pressed)
        return None

      # toggle Sequence And Channel
      if CONTROLS[button] == TOGGLE_CH_SEQ:
        self.active = not self.active
        time.sleep(1)

      # select Channel
      if CONTROLS[button] == CH_SEQ_SELECT:
        # alt_pressed on channel changes moves to next range
        if state.alt_pressed:
          button = button + 3
        self.midi_h.channel = button - 3
      # fx controls
      if CONTROLS[button] == CHANGE_RATE:
        state.knob_controller = CHANGE_RATE
      if CONTROLS[button] == CHANGE_TEMPO_PITCH:
        if state.alt_pressed:
           state.knob_controller = CHANGE_TEMPO
        else:
           state.knob_controller = CHANGE_PITCH

      # active only controls
      if self.active:
        # play Note
        if CONTROLS[button] == NOTE_ON:
            self.midi_h.note_on(button, 0xFF, ch=self.midi_h.channel)
        # next prev actions
        if CONTROLS[button] == PREV:
          # next offset of notes
          self.midi_h.prev_offset()
        if CONTROLS[button] == NEXT:
          # prev offset of notes
          self.midi_h.next_offset()

      # assign controls
      if CONTROLS[button] == TRIM_START:
        if self.active:
          state.knob_controller = TRIM_START
        else:
          state.knob_controller = CHANGE_VOLUME
      if CONTROLS[button] == TRIM_END:
        if self.active:
          state.knob_controller = TRIM_END
        else:
          state.knob_controller = CHANGE_PANNING


    # only play notes when in active control mode
    for button in released:
      if CONTROLS[button] == NOTE_ON:
        if self.active:
            # send regular note off action
            self.midi_h.note_off(button, 0, ch=self.midi_h.channel)

      # only enable alt_pressed when pressed
      if CONTROLS[button] == FUNCTION:
        state.alt_pressed = False

      # only enable save when
      if button ==  PROGRAM_SAVE_SONG:
         if self.save_pending:
           # button was released without saving pack
           self.set_program(PROGRAM_SAVE_SLICES, state.alt_pressed)
         self.save_pending = False
      if button ==  PROGRAM_LOAD_SONG:
         if self.load_pending:
           # button was released without saving pack
           self.set_program(PROGRAM_LOAD_SLICES, state.alt_pressed)
         self.load_pending = False

  def channel(self):
    return self.midi_h.channel

  def set_program(self, prog, alt_pressed):

    prog_val = PROGRAM_APP_VALUE[prog]

    if prog == PROGRAM_BROWSE:
      # always using ch=1 for browse prog
      # and deactivate seq
      self.midi_h.channel = 1
      self.midi_h.program_change(prog_val, ch=1)
      self.active = True
    elif prog == PROGRAM_SAVE_SONG:
      # pending for a combo press
      self.save_pending = True
    elif prog == PROGRAM_LOAD_SONG:
      # pending for a combo press
      self.load_pending = True
    else:
      self.midi_h.program_change(prog_val)
    self.midi_h.reset_offset()

class SequencerButtons:
  def __init__(self, trellis, midi_h, channel):
    self.on_buttons = set()
    self.trellis = trellis
    self.midi_h = midi_h
    self.channel = channel
    self.active = True
    self.last_note = None
    self.frame = 0
    self.auto_next = False
    self.last_note_offset = 0
    self.pattern = [None, None, None, None,
                    None, None, None, None,
                    None, None, None, None,
                    None, None, None, None]

  def show_pattern(self):
    pattern_start = self.frame * GRID_SIZE
    pattern_end = pattern_start + GRID_SIZE
    grid = self.pattern[pattern_start:pattern_end + 1]
    for i in range(GRID_SIZE):
      if grid[i] is not None:
        self.trellis.led[16+ i] = True
      else:
        self.trellis.led[16 + i] = False

  def get_step(self, i):
    return self.pattern[i + (frame * 16)]

  def next_frame(self):
    # increment frame
    self.frame = self.frame + 1

    # brighten for visual indication
    self.trellis.led.fill(False)

    # extend pattern if adding new frame
    if (self.frame * GRID_SIZE) == len(self.pattern):
      self.pattern.extend([None, None, None, None,
                      None, None, None, None,
                      None, None, None, None,
                      None, None, None, None])
    else:
      # show pattern already set to next frame
      self.show_pattern()

  def prev_frame(self):
    # decrement frame
    self.frame = self.frame - 1

    # dim for visual indication
    self.trellis.led.fill(False)

    # cannot be on negative frame
    if (self.frame < 0):
      self.frame = 0

    # show pattern
    self.show_pattern()

  def update(self, state, display_channel):

    # return if this is the display channel but is not active
    # or not the currently active channel
    if not self.active or (display_channel != self.channel):
      return

    just_pressed, released, off_buttons, _ = state.get_buttons()

    # update trellis
    for b in just_pressed:
        # TODO: rm with more girds
        # handle control buttons
        if b < 16:
          # pressing prev/next on sequencer moves the pattern gird
          if CONTROLS[b] == NEXT:
            if state.alt_pressed:
              self.last_note_offset = self.last_note_offset + GRID_SIZE
            else:
              self.next_frame()
          if CONTROLS[b] == PREV:
            if state.alt_pressed:
              self.last_note_offset = self.last_note_offset - GRID_SIZE
            else:
              self.prev_frame()

          # ignoring other controls so far
          continue

        # just let note play when in alt_pressed mode and set as last note
        if state.alt_pressed:
           # NOTE: corresponding note off isn't sent
           note = b + self.last_note_offset
           self.midi_h.note_on(note, 0xFF, ch=self.channel)
           self.last_note = NoteOn(note)
        else:
          # light up buttons not in off set
          self.trellis.led[b] = b not in off_buttons
          last_chan_note = self.midi_h.channel == self.channel and self.last_note or None
          self.pattern[b + (self.frame * GRID_SIZE)  - GRID_SIZE] = self.trellis.led[b] and last_chan_note or None

    # symmetric different update will remove the off_buttons
    # that are already in the list of on_buttons while also
    # adding the new just_pressed buttons to the list
    just_pressed.extend(state.off_buttons)
    state.on_buttons.symmetric_difference_update(just_pressed)

  # play grid step based on pattern
  async def play_step(self, i):

    if not self.active:
      return


    # move to whatever frame we are in
    # when in auto_next
    step = i % len(self.pattern)
    if self.auto_next:
      step_frame = int(step/GRID_SIZE)
      if step_frame != self.frame:
        self.frame = step_frame
        self.show_pattern()

    msg = self.pattern[step]
    if msg is not None:
        self.midi_h.note_on(msg[1], 0xFF, ch=self.channel)

  async def led_step(self, i, display_channel):
    if not self.active:
      return

    # TODO: rm with more grids
    # when display channel is same as seq chan then blink
    if display_channel != self.channel:
      return
    # step is offset to reference second grid
    step = i % GRID_SIZE + GRID_SIZE
    # illuminate current led in step
    n_steps = len(self.pattern)
    if self.pattern[i % n_steps] is None:
      self.trellis.led[step] = True
    last_step = step - 1
    # Wrap around if last step referred to 1st grid
    if last_step < GRID_SIZE:
      last_step = 2*GRID_SIZE - 1

    # deactivate last if not part of pattern
    if self.pattern[last_step + (self.frame * GRID_SIZE) - GRID_SIZE] is None:
      self.trellis.led[last_step] = False
