# Use this file to plot a curve for "charging" the inductor to see how long 
# it takes to switch currents
import sys
import os

sys.path.append(os.path.abspath(".."))  # Add previous directory to pat

import RPi.GPIO as GPIO

import mcp3008
import time
import csv
import RPi.GPIO as GPIO

from filters import Filters

# Initialize ADC
channel = 1
adc = mcp3008.MCP3008()
pwm_pin = 12
pwm_frequency = 500

# set test param
total_time = 0.5 
on_time = 0.1
pwm_start = 0
pwm_stop = 100
sample_freq = 8e3
window = 1
do_median = False # otherwise mean
do_median_mean = False

# set up filter
filt = Filters(window)

# set up PWM
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pwm_pin, GPIO.OUT)
pi_pwm = GPIO.PWM(pwm_pin, pwm_frequency) 
pi_pwm.start(pwm_start)

pwm = 0
# Open a CSV file for writing
with open("../data/inductor_charging_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
#    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Time", "ADC Reading", "Current Reading"])

    t = time.time()
    s_time = time.time()
    while time.time() - t < total_time:
        
        if time.time() - s_time < 1/sample_freq:
            continue
        else:
            s_time = time.time() # time to sample!

        count = adc.read(channel)
        

        if do_median_mean:
            count = filt.add_data_mean_t(count)
        elif do_median:
            count = filt.add_data_median(count)
        else:
            count = filt.add_data_mean(count)

        if time.time() - t >= on_time:
            pi_pwm.ChangeDutyCycle(pwm_stop)
#            pwm = pwm_stop

        m = 0.0201
        b = -10.3652
        current = m * count + b
        writer.writerow([time.time()-t, count, current])

GPIO.cleanup()
