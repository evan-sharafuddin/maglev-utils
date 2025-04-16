# implements pwm sine wave

import RPi.GPIO as GPIO

import mcp3008
from pwm import PWM
import time
import csv
import RPi.GPIO as GPIO
import numpy as np

import sys
import os

sys.path.append(os.path.abspath(".."))  # Add previous directory to pat

from filters import Filters

# Initialize ADC
ir_channel = 0
current_channel=2
adc = mcp3008.MCP3008()
pwm_pin = 18
pwm_frequency = 10000
fs = 5000 # data sampling rate

period = 0.15 # number of seconds that cycle will complete
off_time = period / 2 # time that the magnet is off
pwm_step_time = off_time / 100 # time between stepping down the pwm
pwm_step_size = 1 # step down size for the pwm

on_time = period - off_time
if on_time < 0: 
   print("ERROR: off time must be smaller than period, aborting")
   sys.exit()

switch_cnt = 10
pwm = 100
# max_pwm = 100
# min_pwm = 0

total_time = (switch_cnt + 1) * period 

switch = True

## CREATE SINE WAVE 
t1 = period     # period of the sine wave (in seconds)
t2 = 0.001     # sampling period (in seconds), i.e., 1 kHz sampling rate
duration = total_time # total duration to show (e.g., 2 cycles)

# Time array
t = np.arange(0, duration, t2)

# Frequency = 1 / period
f = 1 / t1

# Sine wave
y = 50*np.cos(2 * np.pi * f * t) + 50
# initialize pwm to be first value in the cosine wave
pwm = y[0]

pipwm = PWM(pwm_pin, pwm_frequency)
pipwm.set_dc(100)
time.sleep(2)
print("start test")

# Load CSV (skip header if you included one)
data = np.loadtxt('adc_to_position_lookup3.csv', delimiter=',') 
adc_counts = data[:, 0].astype(int)
positions = data[:, 1]

filt_ir = Filters(10)
filt_cur = Filters(10)

# Open a CSV file for writing
with open("./data/bounce_test.csv", "w", newline="") as file:
    writer = csv.writer(file)
    # writer.writerow([f"PWM frequency of {pwm_frequency}"])
    writer.writerow(["Time", "PWM", "ADC Reading", "Current Reading", "Position"])
    
    t = time.time()
    sample_time = time.time()
    
    # s_off_time = time.time()
    # s_on_time = time.time()
    # s_pwm_step_time = time.time() 
    # is_on = False # have it turn on first
    s_sine_time = time.time()
    pipwm.set_dc(pwm)
    sine_idx = 1 # already have taken the first value of the cosine, want to start on the second
    
    while time.time() - t <= total_time:
      if time.time() - s_sine_time > t2:
        pwm = y[sine_idx]
        pipwm.set_dc(pwm)
        sine_idx += 1
        s_sine_time = time.time()

        # ## UNCOMMENT FOR CONSTANT PWM
        # pwm = 10
        # pipwm.set_dc(pwm)


      # sampling code
      if time.time() - sample_time > 1/fs:
        sample_time = time.time()

        current_count = adc.read(current_channel)
        current_count = filt_cur.add_data_mean(current_count)

        ir_count=adc.read(ir_channel)
        ir_count = filt_ir.add_data_mean(ir_count)
        ir_count = int( round(ir_count) ) # convert to integer
        #pos_read = positions[adc_counts == ir_count][0]


        # counts += adc.read(channel)
        # ii += 1
        
        # counts = counts / ii # calculate average counts over the second of data collection

        m = 0.0201
        b = -10.3652
        current = m * current_count + b
        curr_time = (time.time() - t) % 60
        #writer.writerow([curr_time, pwm, ir_count, pos_read, current])
        position = positions[adc_counts == ir_count][0]
        writer.writerow([curr_time, pwm, ir_count, current, position])

        # if pwm % 10 == 0 and pwm != 0:
        #   print(".", flush=True)
        # else:
        #   print(".", end = "", flush=True) 

print("end test -- dropping!")
pipwm.set_dc(100)
time.sleep(0.5)


