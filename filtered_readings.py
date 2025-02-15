"""
Implements a live-feed display for ADC readigs for the Maglev testbed

Command line arguments are as follows:

"""


import curses
import time
import mcp3008
import argparse
import atexit
import math
from filters import Filters

import RPi.GPIO as GPIO

SUCCESS = 0 # standard normal exit code
ERR = -1 # standard error exit code

# set up command line arguments
msg = "Displays up to 8 ADC channel readings from MCP3008"
parser = argparse.ArgumentParser(description=msg)

# sampling arguments
parser.add_argument('-w', '--mean_window', type=int, help="Size of moving average window, in samples")
parser.add_argument('-m', '--median_window', type=int, help="Size of median filter window, in samples")
parser.add_argument('-s', '--sps', type=int, help="Sampling rate, in Hz (samples per second)")

# MCP3008 arguments
parser.add_argument('-c', '--channel', type=int, help="Channel numbers to use; each digit cooresponds to a channel (0-7)")
parser.add_argument('-v', '--vdd_hi', action='store_true', help="Enable when MCP3008 powered by 5V line")

# misc arguments
parser.add_argument('-d', '--debug', action='store_true', help="Enable debug messages")
parser.add_argument('-y', '--dummy', action='store_true', help="Enable this to test code without RPi hardware")

args = parser.parse_args()

def main(stdscr):
    
    if not parser.dummy: 
        # initialize ADC
        adc = mcp3008.MCP3008( Vdd_hi=parser.vdd_hi ) # assuming 5 Vdd

    # parse channels between 0 and 7
    channel_str = str(parser.channel)
    channel_list = [ d for d in channel_str if ( d > 0 and d < 7 ) ]
    if len(channel_list) == 0: 
        print("ERROR: Invalid channels provided. Aborting")
        exit(ERR)

    # extract sampling parameters
    sample_period = 1 / parser.sps
    w_mean = parser.mean_window
    w_median = parser.median_window

    # handle GPIO cleanup upon exit
    def _close_pwm():
        GPIO.cleanup()
        print("Cleaned GPIO pins")
    atexit.register(_close_pwm)

    # Initialize curses terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(100)  # Refresh every 100 ms

    height, width = stdscr.getmaxyx()
    info_section_height = 3
    data_section_height = height - info_section_height

    # Create a window for error messages (top part of the screen)
    info_win = curses.newwin(info_section_height, width, 0, 0)
    # Create a window for routine data (bottom part of the screen)
    data_win = curses.newwin(data_section_height, width, info_section_height, 0)
    
    # add info to info_win
    info_win.addstr(0, 0, "Press Ctrl-C to exit program")
    info_win.refresh()
    
    # loop through sampling until Ctrl-C signal
    while True:
        
        # create dictionary to store data for each channel
        data = dict()
        for c in channel_list:
            data[c] = list()

        d_start = time.time()

        while time.time() - d_start < sample_period: # TODO need to check whether sample period is too small, this could result in errors
            for c in channel_list:

                if parser.dummy:
                    data[c].append( round(math.random()*1024) )
                    # simulate some extra time
                    time.sleep(0.01)
                else:
                    data[c].append( adc.read(c) )
        
        d_time = time.time() - d_start
        d_cnt = len(data[channel_list[0]])

        # Filter data
        f_start = time.time()

        disp_dict = dict()
        for c in channel_list:
            disp_dict[c] = Filters.simple_mean(data[c])

        f_time = time.time() - f_start


        # Display data via curses
        # Clear screen to avoid overwriting previous content
        data_win.clear()

        # Create the text string
        text = f"""Num samples (samles): {d_cnt}
                   Sampling time (s)   : {d_time}
                   Filtering time (s)  : {f_time}""" # TODO implicit \n here?
        
        for c in channel_list:
            text += f"Channel {c} reading: {disp_dict}\n"
                   
        
        # BELOW: old code for calculating current reading from current esnsor
        #    \nCurrent value: { ((reading * (pi_5v/1024)) - pi_5v/2) / 0.066}""" # 3.3 Pi voltage (TODO measure
                                                                            # 0.066 mV/A
                                                                            # 10 bit adc -- 1024

        # Add the text to the window at position (1, 1)
        data_win.addstr(0, 0, text)

        # Update the screen
        data_win.refrest()

if __name__ == "__main__":
    curses.wrapper(main)

   