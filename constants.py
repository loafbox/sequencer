from rtmidi.midiconstants import *
FUNCTION = 0xC1
TOGGLE_CH_SEQ = 0xC2
PREV = 0xC3
NEXT = 0xC4
CH_SEQ_SELECT = 0xC5

GRID_SIZE = 16 

CTL_CLOCK_SPEED = 1200 # 0.05 sec


CONTROLS = [PROGRAM_CHANGE, PROGRAM_CHANGE, PROGRAM_CHANGE, PROGRAM_CHANGE,
            FUNCTION, TOGGLE_CH_SEQ, PREV, NEXT,
            CH_SEQ_SELECT, CH_SEQ_SELECT, CH_SEQ_SELECT, CH_SEQ_SELECT,
            CH_SEQ_SELECT, CH_SEQ_SELECT, CH_SEQ_SELECT, CH_SEQ_SELECT,
						NOTE_ON, NOTE_ON, NOTE_ON, NOTE_ON,
						NOTE_ON, NOTE_ON, NOTE_ON, NOTE_ON,
						NOTE_ON, NOTE_ON, NOTE_ON, NOTE_ON,
						NOTE_ON, NOTE_ON, NOTE_ON, NOTE_ON]
