"""
Implements a live-feed display for ADC readigs for the Maglev testbed

Command line arguments are as follows:

"""


import curses
import time
import mcp3008
import argparse
import atexit
import random
import sys
from filters import Filters
##from controller import Controller

SUCCESS = 0 # standard normal exit code
CHANNEL_NOT_INT = 1 
CHANNEL_OUT_OF_BOUNDS = 2

err = dict()
err[CHANNEL_NOT_INT] = "ERROR: Invalid channels provided. Argument must be a set of integers. Aborting"
err[CHANNEL_OUT_OF_BOUNDS] = "ERROR: Invalid channels provided. Channels must be between 0 and 7, inclusive. Aborting"

# set up command line arguments
msg = "Displays up to 8 ADC channel readings from MCP3008"
parser = argparse.ArgumentParser(description=msg)

# sampling arguments
parser.add_argument('-w', '--mean_window', type=int, help="Size of moving average window, in samples")
parser.add_argument('-m', '--median_window', type=int, help="Size of median filter window, in samples")
parser.add_argument('-s', '--sps', type=int, default=5, help="Sampling rate, in Hz (samples per second)")

# MCP3008 arguments
parser.add_argument('-c', '--channel', type=str, help="Channel numbers to use; each digit cooresponds to a channel (0-7)")
parser.add_argument('-v', '--vdd_lo', action='store_true', help="Enable when MCP3008 powered by 3.3V line")

# misc arguments
parser.add_argument('-d', '--debug', action='store_true', help="Enable debug messages")
parser.add_argument('-y', '--dummy', action='store_true', help="Enable this to test code without RPi hardware")
parser.add_argument('-p', '--pwm', action='store_true', help="Enable PWM output on pin 12")
parser.add_argument('-f', '--file', action='store_true', help="Store data points in a file")

args = parser.parse_args()

if not args.dummy:
    import RPi.GPIO as GPIO

def main(stdscr):
    
    if not args.dummy: 
        # initialize ADC
        adc = mcp3008.MCP3008( Vdd_hi=not args.vdd_lo )

    # parse channels between 0 and 7
    channel_str = str(args.channel)
    try: 
        channel_list = [ int(c) for c in channel_str ]
    except ValueError:
        print("ERROR: Invalid channels provided. Argument must be a set of integers. Aborting", flush=True)
        sys.stdout.flush()
        raise SystemExit(CHANNEL_NOT_INT)
    channel_list = [ d for d in channel_list if ( d >= 0 and d <= 7) ]
    if len(channel_list) == 0: 
        raise SystemExit(CHANNEL_OUT_OF_BOUNDS)

    # extract sampling parameters
    sample_period = 1 / args.sps
    w_mean = args.mean_window
    w_median = args.median_window

    # setup PWM
    if args.pwm:
        pwm_pin = 12
        pwm_freq = 20000 # Hz
        duty_cycle = 100 # percent
        
        GPIO.setmode(GPIO.BOARD)
        GPIO.setmode(GPIO.BOARD)		#set pin numbering system
        GPIO.setup(pwm_pin, GPIO.OUT)
        pi_pwm = GPIO.PWM(pwm_pin, pwm_freq)		#create PWM instance with frequency
        pi_pwm.start(duty_cycle)				#start PWM of required Duty Cycle 

    # handle GPIO cleanup upon exit
    def _at_exit():
        if not args.dummy and args.pwm:
            GPIO.cleanup()
            print("Cleaned GPIO pins")

    atexit.register(_at_exit)

    # Initialize curses terminal
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(100)  # Refresh every 100 ms

    height, width = stdscr.getmaxyx()
    info_section_height = 5
    data_section_height = height - info_section_height

    # Create a window for error messages (top part of the screen)
    info_win = curses.newwin(info_section_height, width, 0, 0)
    # Create a window for routine data (bottom part of the screen)
    data_win = curses.newwin(data_section_height, width, info_section_height, 0)
    
    # add info to info_win
    info_win.addstr(0, 0, "Press Ctrl-C to exit program")
    if args.dummy: info_win.addstr(1, 0, "NOTE: dummy mode enabled")
    info_win.addstr(3, 0, "-------")
    info_win.refresh()

    # store file if command line argument set
    if args.file:
        f = [ str() for _ in range(len(channel_list)) ]
        data = [ list() for _ in range(len(channel_list)) ]
        t_list = list()
    
    start  = time.time()

    # loop through sampling until Ctrl-C signal
    # while time.time() - start < 5:
    while True:
        # create dictionary to store data for each channel
        data = dict()
        for c in channel_list:
            data[c] = list()

        d_start = time.perf_counter() # using perf counter here, had some issues with system clock
                                      # returning incorrect values resulting in negative elapsed time

        while time.perf_counter() - d_start < sample_period: # TODO need to check whether sample period is too small, this could result in errors
            for c in channel_list:
                
                if args.dummy:
                    data[c].append( round(random.random()*1024) )
                    # simulate some extra time
                    time.sleep(0.001)

                else:
                    data[c].append( adc.read(c) )
        
        d_time = time.perf_counter() - d_start
        d_cnt = len(data[channel_list[0]])

        # Filter data
        f_start = time.perf_counter()

        disp_dict = dict()
        for ii, c in enumerate(channel_list):
            disp_dict[c] = Filters.simple_mean(data[c])

            if args.file:
                data_point = f"{time.time() - start} {disp_dict[c]}\n"
                f[ii] += data_point
                data[ii].append(disp_dict[c])

        if args.file: t_list.append(time.time() - start)

        f_time = time.perf_counter() - f_start

        # Display data via curses
        # Clear screen to avoid overwriting previous content
        data_win.clear()

        # Create the text string
        text = f"Num samples (samples)     : {d_cnt}\n"  \
               f"Sampling time (s)         : {d_time}\n" \
               f"Filtering time (s)        : {f_time}\n" \
        
        for c in channel_list:
            text += \
               f"Channel {c} reading (0-1023): {disp_dict[c]}\n" \
               f"Current value: { (2.55 - (disp_dict[c] * (5.097/1023))) / 0.185}\n" # 3.3 Pi voltage (TODO measure
                                                                                # 0.066 mV/A
                                                                                # 10 bit adc -- 1024


        # Add the text to the window at position (1, 1)
        data_win.addstr(0, 0, text)

        # Update the screen
        data_win.refresh()


    if args.file:
        for ii, c in enumerate(channel_list):
            file_path = f"./data/c{c}_data.txt"

        with open(file_path, "w") as file:
            file.write(f[ii])

        


if __name__ == "__main__":
    
    try:
        curses.wrapper(main)

    # must print error messages outside of the curses wrapper
    except SystemExit as e:
        print(err[e.code])

    except Exception as e:
        print(f"An error occured: {str(e)}")

   
