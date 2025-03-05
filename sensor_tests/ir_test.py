"""
Old code used for testing the current sensor and PWM current controller
"""

import curses
import time
import mcp3008
import RPi.GPIO as GPIO
import atexit

def main(stdscr):
    # Initialize curses
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)   # Non-blocking input
    stdscr.timeout(500)  # Refresh every 100 ms
    
    # initialize ADC
    adc = mcp3008.MCP3008( Vdd_hi=True ) # assuming 5 Vdd

    # constants
    refresh = 0.1 # time in seconds to refresh reading 
    channel = 7
    pi_5v = 5.05 # NOTE might want to remeasure this every once and a while with multimeter

    # setup PWM
    pwm_pin = 12
    pwm_freq = 1000 # Hz
    duty_cycle = 20 # percent

    GPIO.setmode(GPIO.BOARD)
    GPIO.setmode(GPIO.BOARD)		#set pin numbering system
    GPIO.setup(pwm_pin, GPIO.OUT)
    pi_pwm = GPIO.PWM(pwm_pin, pwm_freq)		#create PWM instance with frequency
    pi_pwm.start(duty_cycle)				#start PWM of required Duty Cycle 

    def _close_pwm():
        GPIO.cleanup()
        print("Cleaned GPIO pins")
    
    atexit.register(_close_pwm)

    while True:

        # get sensor data
        start = time.time()

        sum = 0
        cnt = 0

        while time.time() - start < refresh: 
            sum += adc.read(channel)
            cnt += 1
        
        if cnt == 0:
            reading = -1
        else: 
            reading = sum / cnt

        # Clear screen to avoid overwriting previous content
        stdscr.clear()

        # Create the text string
        text = f"Press Ctrl-C to cancel\n\nADC reading: {reading}" \
               f"\nNum samples: {cnt}"
                                                                           # 10 bit adc -- 1024

        # Add the text to the window at position (1, 1)
        stdscr.addstr(1, 1, text)

        # Update the screen
        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)
