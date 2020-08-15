from RPi import GPIO
from time import sleep

RoAPin = 6
RoBPin = 5
RoSPin = 7 


class Knob:
  def __init__(self):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RoAPin, GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(RoBPin, GPIO.IN,pull_up_down=GPIO.PUD_UP)

    self.value = 64
    self.flag = 0
    self.Last_RoB_Status = 0
    self.Current_RoB_Status = 0


  def get_knob_value(self): 
    self.Last_RoB_Status = GPIO.input(RoBPin)
    while(not GPIO.input(RoAPin)):
      self.Current_RoB_Status = GPIO.input(RoBPin)
      self.flag = 1
    if self.flag == 1:
      self.flag = 0
      if (self.Last_RoB_Status == 0) and (self.Current_RoB_Status == 1):
        self.value = self.value + 1
      if (self.Last_RoB_Status == 1) and (self.Current_RoB_Status == 0):
        self.value = self.value - 1
      return self.value
    else:
       return None


