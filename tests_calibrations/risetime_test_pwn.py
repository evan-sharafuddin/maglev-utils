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
from pwm import PWM

from filters import Filters

# Initialize ADC
channel = 1
adc = mcp3008.MCP3008()
pwm_pin = 12

# set test param
total_time = 0.5
on_time = 0.2
pwm_start = 60
pwm_stop = 30
pwm_freq = 10000;
window = 10
do_median = False # otherwise mean
do_median_mean = True

# set up filter
filt = Filters(window)

pi_pwm = PWM(18, freq=pwm_freq)
pi_pwm.set_dc(pwm_start)

# Open a CSV file for writing
with open(f"../data/riseTimeData{pwm_freq}Hz-risetime_test_{pwm_start}-{pwm_stop}.csv", "w", newline="") as file:
    writer = csv.writer(file)
#    writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Time", "ADC Reading", "Current Reading"])

    t = time.time()
    
    while time.time() - t < total_time:

        count = adc.read(channel)        

        # if do_median_mean:
        #     count = filt.add_data_mean_t(count)
        # elif do_median:
        #     count = filt.add_data_median(count)
        # else:
        #     count = filt.add_data_mean(count)

        if time.time() - t >= on_time:
            pi_pwm.set_dc(pwm_stop)

        m = 0.0201
        b = -10.3652
        current = m * count + b
        writer.writerow([time.time()-t, count, current])
