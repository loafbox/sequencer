import time
import sys
import queue 
import board
import busio
import asyncio
from adafruit_trellis import Trellis
from metronome import Metronome
from midi_handler import MidiHandler  
from buttons import *
from knob import Knob
from RPi import GPIO

# setup midi
midi_h = MidiHandler(ch=1)

# setup trellis
i2c = busio.I2C(board.SCL, board.SDA)
addresses=[0x71, 0x70]

if i2c is not None:
	print("I2C devices found: ", [hex(i) for i in i2c.scan()])

trellis = Trellis(i2c, addresses)
trellis.led.fill(False)
trellis.brightness = 1

# collect all the metronome's callbacks
ctlButtons = ControllerButtons(midi_h)
state = ButtonState()
knob = Knob()

 
# button reconciler 
async def button_handler(clock):

  # add some button chill so we don't spam notes
  global bounce_count
  if bounce_count % 3 != 0:
    bounce_count += 1
    return
  bounce_count = 1

  # get button state
  state.set_buttons(trellis)

  # always check ctl buttons
  curr_ctl_active = ctlButtons.active 
  ctlButtons.update(state, knob)

  # check sequencer note added if ctl notes disabled
  for _, seq in clock.sequencers.items():
    seq.active = not curr_ctl_active
    seq.update(state, clock.display_channel)
 
  # detect mode change
  if curr_ctl_active != ctlButtons.active:
    state.reset_buttons()

    # control and note mode 
    if ctlButtons.active:
      # clear leds
      trellis.led.fill(False)
    else:
      # start a sequencer thread if not already going
      chan = ctlButtons.channel()
      if chan not in clock.sequencers:
        seq = SequencerButtons(trellis, midi_h, chan)
        clock.sequencers[chan] = seq
        clock.display_channel = chan
      else:
        clock.sequencers[chan].show_pattern() 

  # detect chan change
  if clock.display_channel != midi_h.channel:
    if midi_h.channel in clock.sequencers:
      clock.display_channel = midi_h.channel
      state.reset_buttons()
      clock.sequencers[midi_h.channel].show_pattern() 

async def knob_handler(clock):

  # apply knob position to chan
  knob_ctl_val = knob.get_knob_value()
  if knob_ctl_val is not None:
    midi_h.controller_change(0x72, knob_ctl_val)


cbs = [button_handler, knob_handler]

# knob interrupt handler 
  
# set tempo to 160 beats-per-minute
tempo = 320

# create the metronome
metronome = Metronome(tempo=tempo, callbacks=cbs)

# produce the coroutine
metronome_coro = metronome.start()

# asyncio boilerplate to run the coroutine
bounce_count = 1
loop = asyncio.get_event_loop()
loop.run_until_complete(metronome_coro)
