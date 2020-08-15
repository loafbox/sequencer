import asyncio
import time
from typing import Callable, Any, List, Awaitable

CallBack = Callable[[None], Awaitable[Any]]
CallBacks = List[CallBack]

class Metronome:
  def __init__(self, tempo: int, callbacks: CallBacks):
    self.tempo = tempo
    self.callbacks = callbacks
    self.sequencers = {}
    self.display_channel = 1
		# position in frame
    self.pos = 0

  async def start(self):
    offset = 0
    sleep_tot = 0

    while True:
      await asyncio.sleep(0.01)
      sleep_target = max(0, (60.0 / self.tempo - offset))
      sleep_tot = sleep_tot + 0.01 + offset 

      # start timer
      t0 = time.time()


      # sequencer must only run at tempo regardless of clock speed 
      if sleep_tot >= sleep_target:
        for _, seq in self.sequencers.items():
          await(seq.play_step(self.pos))
          await(seq.led_step(self.pos, self.display_channel))
        sleep_tot = 0
        self.pos = self.pos + 1
      else:
		    # send position to callbacks
        for callback in self.callbacks:
          await callback(self)

      # calculate offset
      t1 = time.time()
      offset = t1 - t0
